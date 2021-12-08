from main.models import Elo, Metadata, Game, Constant
import pandas as pd
from datetime import timedelta, datetime
from django.contrib.auth.models import User
from itertools import combinations


def f(x, X, y, Y):
    """
    Funzione che date due coppie di punti e turni ritorna l'esito della partita
    per il giocatore x,X
    """
    return (x > y)+(x == y)*(X < Y)+0.5*(x == y)*(X == Y)


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


def fill_from_latest():
    """
    Fill the Elo table from the latest Elo data.
    """

    #prendo l'id di partenza
    start_date = Elo.objects.order_by(
        '-tour_id__date').first().tour_id.date

    #prendo l'ultimo id dei tornei
    last_tour_date = Metadata.objects.order_by(
        '-date').first().date
    
    #controllo se coincidono e fermo
    if start_date == last_tour_date:
        return

    #prendo i tornei (come lista per zipparli) ordinati per data crescente
    tours = list(
        Metadata.objects.filter(date__gte=start_date).order_by('date')
    )

    #prendo gli utenti (per riempire i vuoti)
    users = list(User.objects.filter(
        is_staff=False).values_list('id'))
    users = [u[0] for u in users] #faccio così perchè users è una lista di tupla

    #li scorro accoppiati
    for prev,curr in zip(tours[:-1], tours[1:]):

        #prendo gli elo di prev
        prev_elos = get_prev_elo(prev)

        #prendo le partite del torneo corrente 
        # --- forse questa parte si può fare senza pandas (e forse più veloce) ---
        cols = ['player_id_1','points_1','turns_1','player_id_2','points_2','turns_2']
        curr_tour = Game.objects.filter(tour_id=curr).values_list(*cols)
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
            id: 0 if total.get(id, True) is True else 1
            for id in users
        }

        #riempio i buchi del totale con 0
        total = {id: total.get(id, 0) for id in users}

        #calcolo gli expected_score
        expected_scores = calculate_expected_scores(
            prev_elos, presences)

        #calcolo gli elo nuovi
        curr_elos = calculate_elo(
            prev_elos, total, expected_scores, presences)

        #salvo gli elo
        for id, elo in curr_elos.items():
            player = User.objects.get(id=id)
            Elo.objects.create(player_id=player, tour_id=curr, elo=elo)


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
    pass


def generate_tour_table(get_data):
    '''
    Funzione che presi in ingresso un dizionario di id:'present'
    di partecipanti al torneo restuisce le tuple per generarne
    la tabella.
    '''

    #inizializzo per il caso base (no dati)
    players = User.objects.filter(is_staff=False)
    warning = ''
    presences = {
        player: False
        for player in players
    }
    tour_table = []
    num_players = 0

    #recupero la data iniziale del campionato e aumento di 1 giorno
    #e converto in stringa per il formato della data
    min_date = Metadata.objects.order_by(
        'date').first().date+timedelta(days=1)
    min_date = min_date.strftime('%Y-%m-%d')
    
    #se get_data è vuoto ritorno
    if not get_data:
        return warning, presences, tour_table, min_date, num_players
    #se non c'è 'presences' ritorno
    if 'presences' not in get_data:
        warning = 'Hai inviato una richiesta non valida, riprova.'
        return warning, presences, tour_table, min_date, num_players

    #poppo 'presences'
    get_data.pop('presences')
    
    #se le misure son sbagliate
    if len(get_data) > len(players) or len(get_data) < 2:
        warning = 'Hai inserito un numero sbagliato di giocatori, riprova.'
        return warning, presences, tour_table, min_date , num_players

    #a questo punto so che i dati han lunghezza corretta
    #e 'presences' è presente

    #inizializzo i presenti a []
    present_players = []

    for key in get_data:

        try:
            #trasformo la key ad int
            key = int(key)
            #prendo il giocatore dai giocatori
            player = players.get(id=key)
            #lo aggiungo ai presenti
            present_players.append(player)

        except ValueError:  # se non è un numero
            warning = 'hai inserito un id non numerico'
            break
        except User.DoesNotExist: #se non c'è l'utente
            warning = 'il giocatore con id {} non esiste'.format(key)
            break

    #se ho incontrato un errore ritorno
    if warning:
        return warning, presences, tour_table, min_date, num_players

    #se non ho incontrato errori
    #setto presences scorrendo i presenti
    for player in present_players:
        presences[player] = True

    #salvo il numero di presenti
    num_players = len(present_players)

    #creo la tabella
    
    #genero tutte le combinazioni
    tour_table = list(combinations(present_players, 2))

    return warning, presences, tour_table, min_date, num_players

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






















    
