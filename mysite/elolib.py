from main.models import Elo, Metadata, Game, Constant, Albo
from django.contrib.auth.models import User
from django.contrib import messages
from django.template.loader import render_to_string
import pandas as pd
import numpy as np
import os, json
from random import shuffle, sample
from plotly.express import line
from datetime import timedelta, datetime
from itertools import combinations


def f(x, X, y, Y):
    """
    Funzione che date due coppie di punti e turni ritorna l'esito della partita
    per il giocatore x,X
    """
    try:
        res = (x > y)+(x == y)*(X < Y)+0.5*(x == y)*(X == Y)
    except:
        res = 0
    return res


def p(x, X, y, Y):
    '''
    Funzione che calcola la percentuale di x in x+y
    anche per numeri negativi.
    Se entrambi 0 si appoggia ai turni.
    '''
    #se uno di questi è None ritorno 0
    if x is None or y is None: return 0
    #se entrambi sono 0 e i turni sono definiti torno l'esito
    if x == 0 and y == 0 and X is not None and Y is not None:
        return f(x,X,y,Y)
    #somma positiva
    if x+y > 0:
        return int(100*x/(x+y))
    #somma negativa
    if x+y<0: 
        return int(100*(1-x/(x+y)))
    #se a somma 0
    if x+y==0:
        #se entrambi 0
        if x==0 and y==0: return 0
        #se complementari
        elif x>0: return 200
        elif x<0: return -100
    

def calculate_expected_scores(start_elos, presences):
    '''
    Funzione che calcola gli expected_score per ogni giocatore
    '''

    #unisco start_elos e presences in un unico dict
    #id : (elo,presence)
    elos = {
        id: (start_elos[id], presences[id])
        for id in start_elos.keys()
    }

    #calcolo gli expected_score come somma dei rapporti di probabilità di tutti gli altri giocatori
    expected_scores = {
        id: sum([other_x[1]*(1/(1+10**((other_x[0]-x[0])/400)))
                 for other_id, other_x in elos.items() if other_id != id
                 ])*x[1]
        for id, x in elos.items()
    }

    return expected_scores

def get_K(presences):
    '''
    Funzione che calcola il K in base alle presenze
    '''

    #query che recupera il K originale
    K = Constant.objects.all().values_list('k')[0][0]

    #query che recupera il numero di giocatori totale
    n = User.objects.filter(is_staff=False).count()

    return K*presences/n

def calculate_elo(elo, outcomes, expected, presences):

    #calcolo la differenza di expected_score elemento per elemento
    step = {
        id: outcomes[id] - expected[id]
        for id in outcomes.keys()
    }

    #calcolo il K da usare
    K = get_K(sum(presences.values()))

    #calcolo gli step
    step = {
        id: K*step[id]
        for id in step.keys()
    }

    #aggiorno gli elo
    elo = {
        id: elo[id] + step[id]
        for id in elo.keys()
    }

    return elo

def get_prev_elo(prev):
    '''
    Funzione che recupera gli elo precedenti
    '''
    #recupero gli elo di prev
    elos = Elo.objects.filter(tour_id=prev)
    #se vuoto
    if not elos:
        #prendo il torneo prima
        prev = Metadata.objects.filter(date__lt=prev.date).order_by('-date').first()
        #chiamo la funzione ricorsivamente
        return get_prev_elo(prev)
    #altrimenti ritorno il dict id:elo
    return {x.player_id.id: x.elo for x in elos}

def fill_elo():
    """
    Fill the Elo table.
    """

    #devo trovare il primo torneo che non appare negli elo
    #1) prendo i metadata degli elo
    elo_meta = list(Elo.objects.all().order_by('tour_id__date').values_list('tour_id').distinct())
    elo_meta = [Metadata.objects.get(tour_id=x[0]) for x in elo_meta]
    #2) prendo i metadata dei tornei
    tour_meta = list(Metadata.objects.all().order_by('date'))
    #3)trovo l'ultimo in comune
    # (escludendo il primo torneo, quello con 1500, perchè non c'è nessun precedente)
    last_common = tour_meta[0]
    for elo,tour in zip(elo_meta[1::], tour_meta[1::]):
        if elo==tour:
            last_common = elo
        else:
            break
    #elimino gli eventuali elo successivi
    Elo.objects.filter(tour_id__date__gt=last_common.date).delete()

    #prendo gli utenti (per riempire i vuoti)
    users = User.objects.filter(
        is_staff=False)

    #scorro i metadata da last_common in poi
    for tour in tour_meta[tour_meta.index(last_common)+1:]:

        #prendo gli elo di prev
        prev_elos = Elo.objects.filter(tour_id__date__lt=tour.date).order_by('-tour_id__date')[:len(users)]
        prev_elos = {entry.player_id.id: entry.elo for entry in prev_elos}

        #prendo le partite del torneo corrente 
        # --- forse questa parte si può fare senza pandas (e forse più veloce) ---
        cols = ['player_id_1','points_1','turns_1','player_id_2','points_2','turns_2']
        curr_tour = Game.objects.filter(tour_id=tour.tour_id).values_list(*cols)
        curr_tour = pd.DataFrame(list(curr_tour), columns=cols)

        #se il torneo non è completo, lo salto
        if curr_tour.isnull().values.any():
            continue

        #costruisco gli outcome su 2 colonne
        outcome = pd.DataFrame()
        outcome['player_id'] = curr_tour['player_id_1'].append(curr_tour['player_id_2'])
        outcome['outcome'] = curr_tour.apply(lambda x: f(
            x.points_1, x.turns_1, x.points_2, x.turns_2), axis=1).append(
            curr_tour.apply(lambda x: f(x.points_2, x.turns_2, x.points_1, x.turns_1), axis=1)
            )

        #trovo il totale
        total = outcome.groupby('player_id').sum().reset_index()
        #trasformo in dict id:totale
        total = {id: total for id, total in 
            zip( total['player_id'].to_list(), total['outcome'].to_list())
        }

        #creo il dict delle presenze (sfruttando quello dei totali)
        presences = {
            user.id: 0 if total.get(user.id, True) is True else 1
            for user in users
        }

        #riempio i buchi del totale con 0
        total = {user.id: total.get(user.id, 0) for user in users}

        #calcolo gli expected_score
        expected_scores = calculate_expected_scores(
            prev_elos, presences)

        #calcolo gli elo nuovi
        curr_elos = calculate_elo(
            prev_elos, total, expected_scores, presences)

        #salvo gli elo
        for id, elo in curr_elos.items():
            player = users.get(id=id)
            Elo.objects.create(player_id=player, tour_id=tour, elo=elo)

def reset_elo():
    '''
    Funzione che resetta gli Elo a 1500 per tutti i giocatori
    '''
    #resetto tutto
    Elo.objects.all().delete()
    #prendo tutti gli utenti e la prima data
    users = User.objects.filter(is_staff=False)
    meta = Metadata.objects.get(tour_id=1)
    #scorro gli utenti ed aggiungo l'elo iniziale
    for user in users:
        Elo.objects.create(player_id=user, tour_id=meta)

def generate_tour_table(get_data):
    '''
    Funzione che presi in ingresso un dizionario di id:'present'
    di partecipanti al torneo restuisce le tuple per generarne
    la tabella.
    '''

    #inizializzo per il caso base (no dati)
    players = User.objects.filter(is_staff=False)
    context = {
        'presences': {p:False for p in players},
        'warning': None,
        'combos':None
    }
    
    #se get_data è vuoto ritorno
    if not get_data:
        return context
    #se non c'è 'presences' ritorno il warning
    if 'presences' not in get_data:
        context['warning'] = 'Hai inviato una richiesta non valida, riprova.'
        return context

    #estraggo 'presences'
    get_data.pop('presences')
    
    #se le misure son sbagliate
    if len(get_data) > len(players) or len(get_data) < 2:
        context['warning'] = 'Hai inserito un numero sbagliato di giocatori, riprova.'
        return context

    #a questo punto so che i dati han lunghezza corretta
    #e 'presences' è presente

    #inizializzo i presenti a []
    present_players = []

    for key in get_data:

        try:
            #trasformo la key ad int
            key = int(key)
            #prendo il giocatore dall'id
            player = players.get(id=key)
            #lo aggiungo ai presenti
            present_players.append(player)

        except ValueError:  # se non è un numero
            context['warning']= 'hai inserito un id non numerico'
            break
        except User.DoesNotExist: #se non c'è l'utente
            context['warning'] = 'il giocatore con id {} non esiste'.format(key)
            break

    #se ho incontrato un errore ritorno
    if context['warning']:
        return context

    #se non ho incontrato errori
    #setto presences scorrendo i presenti
    for player in present_players:
        context['presences'][player] = True

    #salvo il numero di presenti
    context['num_players'] = len(present_players)

    #creo la tabella
    
    #genero tutte le combinazioni
    combos = list(combinations(present_players, 2))
    #rendo liste e mischio
    combos = [sample(list(c),2) for c in combos]
    #mischio la lista
    shuffle(combos)
    #mischio le singole tuple
    context['combos'] = combos

    #recupero la data iniziale del campionato e aumento di 1 giorno
    #e converto in stringa per il formato della data
    min_date = Metadata.objects.order_by(
        'date').first().date+timedelta(days=1)
    context['min_date'] = min_date.strftime('%Y-%m-%d')

    return context

def save_tour(data):
    '''
    Funzione che salva un torneo.
    '''

    #mi libero del token
    data.pop('csrfmiddlewaretoken')

    #prendo la data e la converto in datetime (avrà sempre ora = 0)
    #togliendola da data (non so perchè ma è una lista)
    tour_date = datetime.strptime(data.pop('date')[0], '%Y-%m-%d')
    #prendo il metadata con stessa data e ora più recente
    meta = Metadata.objects.filter(date__date=tour_date).order_by('-date__time').first()
    #se esiste
    if meta:
        #aggiungo il tempo già passato più 1 ora
        tour_date = tour_date +timedelta(hours=meta.date.hour)+timedelta(hours=1)
    
    #vedo quanti giocatori ci sono
    n = int(data['player_num'])
    
    #creo i metadata
    meta = Metadata.objects.create(
        date=tour_date,
        N = n
    )

    #genero le stringhe per accedere ai dati
    #int perchè la divisione da float
    n =int(n*(n-1)/2)
    matches = ['M'+str(x) for x in range(1,n+1)]

    #funzione per trasformare una stringa in int o None
    def to_int(string):
        try:
            return int(string)
        except ValueError:
            return None
    
    #scorro i match
    for match in matches:

        #prendo il giocatore 1
        player_id_1 = int(data[match+'_player1'])
        player_id_1 = User.objects.get(id=player_id_1)
        #prendo i punti 1
        points_1 = to_int(data[match+'_points1']) 
        #prendo i turni 1
        turns_1 = to_int(data[match+'_turns1'])

        #prendo il giocatore 2
        player_id_2 = int(data[match+'_player2'])
        player_id_2 = User.objects.get(id=player_id_2)
        #prendo i punti 2
        points_2 = to_int(data[match+'_points2'])
        #prendo i turni 2
        turns_2 = to_int(data[match+'_turns2'])

        #creo il match
        Game.objects.create(
            player_id_1 = player_id_1,
            points_1 = points_1,
            turns_1 = turns_1,
            player_id_2 = player_id_2,
            points_2 = points_2,
            turns_2 = turns_2,
            tour_id = meta
        )

    #ritorno il metadata per redirect
    return meta

def get_tour(id):
    '''
    Funzione che restituisce i dati di un torneo dal suo id.
    '''

    #inizializzo le variabili
    warning = ''

    #prendo i metadata (nel caso non esista restituisco warning)
    try:
        if id==1: raise Exception
        meta = Metadata.objects.get(tour_id=id)
    except:
        warning = 'Il torneo con id {} non esiste'.format(id)
        return {'warning':warning}
        
    #prendo le partite del torneo
    matches = Game.objects.filter(tour_id=id)
    #Trasformo in dataframe
    cols =[
        'player_id_1',
        'player_id_1__username',
        'points_1',
        'turns_1',
        'player_id_2',
        'player_id_2__username',
        'points_2',
        'turns_2'
    ]
    matches = pd.DataFrame(matches.values_list(*cols),columns=cols)
    #creo la colonna 'outcome_1'
    matches['outcome_1'] = matches.apply(lambda x: f(
        x.points_1, x.turns_1, x.points_2, x.turns_2), axis=1)
    matches['outcome_2'] = matches.apply(lambda x: f(x.points_2, x.turns_2,
        x.points_1, x.turns_1), axis=1)
    #creo la colonna 'percent_1' delle percentuali
    matches['percent_1'] = matches.apply(lambda x: p(
        x.points_1, x.turns_1, x.points_2, x.turns_2), axis=1)
    matches['percent_2'] = matches.apply(lambda x: p(
        x.points_2, x.turns_2, x.points_1, x.turns_1), axis=1)

    #creo i totali
    totals = pd.DataFrame()
    totals['player_id'] = matches['player_id_1'].append(matches['player_id_2'])
    totals['username'] = matches['player_id_1__username'].append(matches['player_id_2__username'])
    totals['outcome'] = matches['outcome_1'].append(matches['outcome_2'])
    totals['points'] = matches['points_1'].append(matches['points_2'])
    totals['percent'] = matches['percent_1'].append(matches['percent_2'])
    #sommo per id
    totals = totals.groupby(['player_id','username']).sum().reset_index()
    #ordino per outcome
    totals = totals.sort_values(by=['outcome','percent'],ascending=[False,False])
    


    #recupero la data iniziale del campionato e aumento di 1 giorno
    #e converto in stringa per il formato della data
    min_date = Metadata.objects.order_by(
        'date').first().date+timedelta(days=1)
    min_date = min_date.strftime('%Y-%m-%d')

    #prendo il torneo prima
    try:
        tour_before = Metadata.objects.filter(date__lt=meta.date).order_by('-date').first()
        if tour_before.tour_id==1: raise Exception
        tour_before = tour_before.tour_id
    except:
        tour_before = None
    
    #prendo il torneo dopo
    try:
        tour_after = Metadata.objects.filter(date__gt=meta.date).order_by('date').first()
        tour_after = tour_after.tour_id
    except:
        tour_after = None

    return {
        'warning':warning, 
        'meta':meta,
        'matches':matches.replace(np.NaN, pd.NA).where(matches.notnull(), None),
        'totals':totals,
        'min_date':min_date,
        'previous':tour_before,
        'next':tour_after
    }

def modify_tour(request):
    '''
    Funzione che modifica un torneo.
    '''

    data = request.POST.copy()
    #mi libero del token
    data.pop('csrfmiddlewaretoken')

    #inizializzo il success
    success = None

    #prendo l'id del torneo
    tour_id = int(data.pop('save')[0])
    #prendo i metadata corrispondenti
    meta = Metadata.objects.get(tour_id=tour_id)

    #prendo quella del post
    tour_date = datetime.strptime(data.pop('date')[0], '%Y-%m-%d')

    #se la data è diversa da quella del torneo
    if tour_date.date() != meta.date.date():

        #prendo il metadata con stessa data e ora più recente
        old_meta = Metadata.objects.filter(
            date__date=tour_date.date()
            ).order_by('-date__time').first()
        #se esiste
        if old_meta:
            #aggiungo il tempo già passato più 1 ora
            tour_date = tour_date + \
                timedelta(hours=old_meta.date.hour)+timedelta(hours=1)
        
        #aggiorno i metadati
        meta.date = tour_date
        meta.save()
        #salvo il success
        success = 'Data modificata con successo'
    
    #definisco le colonne
    cols = ['player_id_1','points_1','turns_1','player_id_2','points_2','turns_2']
    
    #prendo le partite del torneo
    matches = Game.objects.filter(tour_id=tour_id)

    #genero le stringhe
    n = int(meta.N*(meta.N-1)/2)
    match_strings = ['M'+str(x) for x in range(1, n+1)]

    #funzione per trasformare una stringa in int o None
    def to_int(string):
        try:
            return int(string)
        except ValueError:
            return None

    #zippo insieme (hanno per forza lo stesso ordine)
    for string,match_tuple,match in zip(match_strings,matches.values_list(*cols),matches):

        #prendo l'id del giocatore 1
        player_id_1 = int(data[string+'_player1'])
        #prendo i punti 1
        points_1 = to_int(data[string+'_points1']) 
        #prendo i turni 1
        turns_1 = to_int(data[string+'_turns1'])

        #prendo l'id del giocatore 2
        player_id_2 = int(data[string+'_player2'])
        #prendo i punti 2
        points_2 = to_int(data[string+'_points2'])
        #prendo i turni 2
        turns_2 = to_int(data[string+'_turns2'])

        #raccolgo
        entry = (player_id_1,points_1,turns_1,player_id_2,points_2,turns_2)

        #confronto i dati, se uguali salto
        if entry == match_tuple:
            continue

        #aggiorno i dati se non vuoti (cioè None, importante usare is not)
        if entry[1] is not None: match.points_1 = entry[1]
        if entry[2] is not None: match.turns_1 = entry[2]
        if entry[4] is not None: match.points_2 = entry[4]
        if entry[5] is not None: match.turns_2 = entry[5]
        #salvo il match
        match.save()

        success = 'Modifica effettuata con successo'

    #aggiungo il success ai messaggi
    messages.success(request, success)

def delete_tour(id):
    '''
    Funzione che elimina un torneo.
    '''

    #prendo i metadata,partite del torneo e Elo successivi
    meta = Metadata.objects.get(tour_id=id)
    matches = Game.objects.filter(tour_id=id)
    elos = Elo.objects.filter(tour_id__date__gte=meta.date)

    #elimino 
    elos.delete()
    matches.delete()
    meta.delete()
    
def pivot_elo():

    #prendo gli elo con data, nome ed elo
    elo = Elo.objects.all().values_list('tour_id__date', 'player_id__username', 'elo')
    #creo il dataframe rinominando le colonne
    elo = pd.DataFrame(list(elo), columns=['date', 'name', 'elo'])
    
    #faccio il pivot su date e la mantengo come colonna (.reset_index())
    elo = elo.pivot(index='date', columns='name', values='elo').reset_index()

    #rinomino la colonna
    elo = elo.rename({'date': 'Data'}, axis=1)
    #formatto la data come giorno-mese
    elo['Data'] = elo['Data'].dt.strftime('%d-%m')

    #prendo l'header della tabella
    header = list(elo.columns)
    #prendo i dati come lista di tuple (vedi https://stackoverflow.com/a/44350260/13373369)
    data = list(zip(*map(elo.get, elo)))
    #creo il context
    context = {
        'header': header,
        'data': data
    }
    
    return context

def update_graph():

    #riempio l'elo
    fill_elo()

    #li prendo come dataframe
    df = pd.DataFrame(
        Elo.objects.all().values_list('tour_id__date','player_id__username','elo'),
        columns=['Data','Giocatore','Elo']
    )

    #plotto
    fig = line(
        df, x='Data', y='Elo', color='Giocatore',
        title='Grafico Elo',
        template='plotly_dark',
        line_shape='spline',
        markers=True
    )
    #
    #path
    graph_path = 'mysite/templates/elo_graph.html'
    #se non esiste la directory la creo
    if not os.path.exists(os.path.dirname(graph_path)):
        os.makedirs(os.path.dirname(graph_path))
    #se non c'è il file lo creo
    if not os.path.isfile(graph_path):
        with open(graph_path, 'w'): pass
    #salvo il grafico
    fig.write_html(
        file = graph_path,
        include_plotlyjs = 'cdn',
        include_mathjax = False,
        full_html = False
    )

def serve_graph():
    #apro il grafico
    with open('mysite/templates/elo_graph.html', 'r') as f:
        return {'graph_code':f.read()}

def tournaments_by_date():

    tours = list(Metadata.objects.order_by('-date').values_list('date','tour_id'))

    #scorro e ritorno tutti tranne il primo
    #(cioè l'ultimo in quest'ordine)
    return [
        (
            tour[0].strftime('%d-%m'),
            int(tour[0].hour)+1,
            tour[1]
        )
        for tour in tours[:-1]
    ]

def get_leaderboard():

    #prendo l'ultimo torneo dagli elo
    meta = Elo.objects.order_by('-tour_id__date').first()

    #elo corrispondenti
    elos = Elo.objects.filter(tour_id=meta.tour_id).order_by('-elo')
    #arrotondo
    elos = [(elo.player_id.username,int(round(elo.elo))) for elo in elos]

    return {
        'elos': elos
    }

def get_variations():
    
    #prendo gli elo con data, nome ed elo
    context = pivot_elo()

    df = pd.DataFrame(context['data'], columns=context['header'])

    #prendo le colonne su cui fare i conti
    cols = context['header'][1:]

    #faccio la differenza, escludo la prima e ricasto ad int
    df[cols] = df[cols].diff()
    df = df[1:]
    #arrotondo
    df[cols] = df[cols].round(1)

    #creo i dataframe booleani di mvp e mongo
    mvp_df = df[cols].isin(df[cols].max(axis=1))
    mongo_df = df[cols].isin(df[cols].min(axis=1))

    #prendo le somme
    mvps = mvp_df.sum(axis=0)[cols]
    mongos = mongo_df.sum(axis=0)[cols]

    #prendo i nomi riga per riga
    df['MVP'] = mvp_df.apply(lambda x: ', '.join([cols[i] for i in range(len(x)) if x[i]]), axis=1)
    df['Mongo'] = mongo_df.apply(lambda x: ', '.join([cols[i] for i in range(len(x)) if x[i]]), axis=1)

    #trovo massimi e minimi globali
    max_mvp = df[cols].max().max()
    min_mong = df[cols].min().min()
    #trovo i nomi corrispondenti
    max_mvp_name = df[cols].max().idxmax() 
    min_mong_name = df[cols].min().idxmin()
    #prendo header e data
    header = list(df.columns)
    data = list(zip(*map(df.get, df)))

    return {
        'header': header,
        'mvps': mvps,
        'mongos': mongos,
        'data': data,
        'max_mvp': max_mvp,
        'min_mong': min_mong,
        'max_mvp_name': max_mvp_name,
        'min_mong_name': min_mong_name
    }

def get_album():

    #prendo gli albi
    albums = Albo.objects.all()

    #prendo il numero di utenti
    n_users = User.objects.filter(is_staff=False).count()

    #divido in categorie
    albums = {
        'Campioni '+str(x-1)+'/'+str(x-1): albums.filter(number=x)
        for x in range(3,n_users+1)
    }

    return {'albums':albums}
    
def save_album(post_data):

    #prendo i dati
    player_id = User.objects.get(id=post_data['player_id'])
    tour_id = Metadata.objects.get(tour_id=post_data['tour_id'])
    #prendo l'album
    try:
        album = Albo.objects.get(player_id=player_id, tour_id=tour_id)
    except:
        album = None
    if not album:
        Albo.objects.create(
            player_id=player_id,
            number=tour_id.N,
            tour_id=tour_id
        )

def new_album_form():

    #prendo i giocatori
    players = User.objects.filter(is_staff=False)
    #prendo i tornei
    tours = tournaments_by_date()

    return {
        'players': players,
        'tours': tours
    }

def get_expected_score(get_data):

    #prendo i giocatori
    players = User.objects.filter(is_staff=False).order_by('id')

    #prendo gli ultimi elo disponibili
    elos = Elo.objects.order_by('-tour_id__date', 'player_id')[:len(players)]

    context = {
        'players': players,
        'presences': {p.id:0 for p in players},
        'old_elos': {e.player_id.id: e.elo for e in elos},
        'warning': None,
        'expected': None,
        'outcomes': None,
        'new_elos': None
    }

    #se get_data è vuoto ritorno
    if not get_data:
        return context

    #prendo gli input dei presenti
    presences_input = [key.split('p_')[-1] for key in get_data if key.startswith('p_')]
    #se le misure son sbagliate
    if len(presences_input) > len(players) or len(presences_input) < 2:
        context['warning'] = 'Hai inserito un numero sbagliato di giocatori, riprova.'
        return context

    #estraggo i presenti
    present_players = []

    for key in presences_input:

        try:
            #trasformo la key ad int
            key = int(key)
            #prendo il giocatore dall'id
            player = players.get(id=key)
            #lo aggiungo ai presenti
            present_players.append(player)

        except ValueError:  # se non è un numero
            context['warning']='hai inserito un id non numerico'
            return context
        except User.DoesNotExist:  # se non c'è l'utente
            context['warning']='il giocatore con id {} non esiste'.format(key)
            return context

    #setto presences scorrendo i presenti
    for player in present_players:
        context['presences'][player.id] = 1

    #calcolo gli expected scores
    context['expected'] = calculate_expected_scores(context['old_elos'], context['presences'])

    #vedo se hanno inserito degli outcome
    if not get_data.get('outcome'):
        return context

    #prendo gli input degli outcome
    outcome_input = [key.split('o_')[-1] for key in get_data if key.startswith('o_')]
    
    #se le misure son sbagliate
    if len(outcome_input) > len(players) or len(outcome_input) < 2:
        context['warning'] = 'Hai inserito un numero sbagliato di giocatori, riprova.'
        return context
    
    #estraggo gli outcome
    outcomes= {}

    def to_float(string):
        try:
            string.replace(',','.')
            return float(string)
        except ValueError:
            return 0

    for key in outcome_input:
    
        try:
            #casto la key dentro così la mantengo stringa
            player = players.get(id=int(key))
            #casto a float
            outcome = to_float(get_data.get('o_'+key))
            #lo aggiungo agli outcome
            outcomes[player.id] = outcome

        except ValueError as e:  # se non è un numero
            context['warning']='hai inserito un id non numerico'
            return context
        except User.DoesNotExist:  # se non c'è l'utente
            context['warning']='il giocatore con id {} non esiste'.format(key)
    
    #metto gli outcome nel context
    context['outcomes'] = {id: (str(outcome).replace(',','.'), context['presences'][id]) for id, outcome in outcomes.items()}
    
    #calcolo il nuovo elo
    context['new_elos'] = calculate_elo(
        context['old_elos'], outcomes, context['expected'], context['presences'])

    #ritorno il context
    return context

def get_tour_ajax(id):

    tour = get_tour(id)

    if tour['warning']:
        warning = render_to_string('main/warning.html',tour)
        return {'warning':warning}

    #aggiorno la data
    date = tour['meta'].date.strftime('%Y-%m-%d')

    #creo l'array
    array = [ 
        [
            [t[1],t[3], t[4]],
            [t[5],t[7], t[8]]
        ] 
        for t in tour['matches'].itertuples()
    ]
    #flattening
    array = sum(array,[])
    #trasformo in stringhe
    array = [ 
        [ str(int(x)) if x is not None else '' for x in t]
        for t in array]

    #creo l'array dei totals
    totals = [
        [t[2],str(int(t[4]))+'%',str(t[3])]
        for t in tour['totals'].itertuples()
    ]

    #ritorno
    return {
        'warning':tour['warning'],
        'date':date,
        'array':array,
        'totals':totals
    }

def update_tour_ajax(request, id):
    '''
    Funzione che modifica un torneo.
    '''

    data = request.POST.copy()
    #mi libero del token
    data.pop('csrfmiddlewaretoken')

    #prendo l'id del torneo
    tour_id = id
    #prendo i metadata corrispondenti
    meta = Metadata.objects.get(tour_id=tour_id)

    #prendo quella del post
    tour_date = datetime.strptime(data.pop('date')[0], '%Y-%m-%d')

    #se la data è diversa da quella del torneo
    if tour_date.date() != meta.date.date():

        #prendo il metadata con stessa data e ora più recente
        old_meta = Metadata.objects.filter(
            date__date=tour_date.date()
        ).order_by('-date__time').first()
        #se esiste
        if old_meta:
            #aggiungo il tempo già passato più 1 ora
            tour_date = tour_date + \
                timedelta(hours=old_meta.date.hour)+timedelta(hours=1)

        #aggiorno i metadati
        meta.date = tour_date
        meta.save()

    #definisco le colonne
    cols = ['player_id_1', 'points_1', 'turns_1',
            'player_id_2', 'points_2', 'turns_2']

    #prendo le partite del torneo
    matches = Game.objects.filter(tour_id=tour_id)

    #funzione per trasformare una stringa in int o None
    def to_int(string):
        try:
            return int(string)
        except ValueError:
            return None

    #prendo l'array delle partite
    array = json.loads(data.pop('array')[0])
    #lo accoppio a due a due
    array = [ x+y for x,y in zip(array[::2],array[1::2])]

    #zippo insieme (hanno per forza lo stesso ordine)
    for array_row, match_tuple, match in zip(array, matches.values_list(*cols), matches):

        #prendo l'id del giocatore 1
        player_id_1 = int(array_row[0])
        #prendo i punti 1
        points_1 = to_int(array_row[1])
        #prendo i turni 1
        turns_1 = to_int(array_row[2])

        #prendo l'id del giocatore 2
        player_id_2 = int(array_row[3])
        #prendo i punti 2
        points_2 = to_int(array_row[4])
        #prendo i turni 2
        turns_2 = to_int(array_row[5])

        #raccolgo
        entry = (player_id_1, points_1, turns_1,
                 player_id_2, points_2, turns_2)

        #confronto i dati, se uguali salto
        if entry == match_tuple:
            continue

        #aggiorno i dati se non vuoti (cioè None, importante usare is not)
        if entry[1] is not None:
            match.points_1 = entry[1]
        if entry[2] is not None:
            match.turns_1 = entry[2]
        if entry[4] is not None:
            match.points_2 = entry[4]
        if entry[5] is not None:
            match.turns_2 = entry[5]
        #salvo il match
        match.save()

        success = 'Modifica effettuata con successo'























    
