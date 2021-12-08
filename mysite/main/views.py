from django.shortcuts import render, redirect
from threading import Thread
from elolib import fill_from, reset_elo, generate_tour_table, \
    save_tour,  get_tour,  modify_tour, pivot_elo,  update_graph, \
    tournaments_by_date, delete_tour

# Create your views here.
def index(request):
    return render(request, "main/index.html")

def elo_table(request):

    #se post
    if request.method == 'POST':
        #se è stato premuto il bottone "Resetta Elo"
        if request.POST.get('reset_elo'):
           reset_elo()
           pass
        #se è stato premuto il bottone "Aggiorna Elo"
        if request.POST.get('update_elo'):
            #aggiorno gli elo
            fill_from()
            pass

    elo = pivot_elo()

    #formatto la data come giorno-mese
    elo['Data'] = elo['Data'].dt.strftime('%d-%m')
    #arrotondo i punteggi
    elo = elo.round({col: 0 for col in elo.columns[1::]})
    #casto a int
    for col in elo.columns[1::]:
        elo[col] = elo[col].astype(int)

    
    #prendo l'header della tabella
    header = list(elo.columns)
    #prendo i dati come lista di tuple (vedi https://stackoverflow.com/a/44350260/13373369)
    data = list(zip(*map(elo.get, elo)))
    #creo il context
    context = {
        'header': header,
        'data': data
    }

    return render(request, "main/elo_table.html", context=context)

def new_tournament(request):

    #se GET
    if request.method == 'GET':

        warning, presences, tour_table, min_date, num_players = generate_tour_table(request.GET.copy())
        
        #costruisco il context
        context = {
            'warning': warning,
            'presences': presences,
            'combos': tour_table,
            'min_date': min_date,
            'num_players': num_players
        }

        return render(request, "main/new_tournament.html", context=context)

    #se POST
    if request.method == 'POST':
        
        #i dati inseriti sono già validi grazie all'html
        new_meta = save_tour(request.POST.copy())
        #aggiorno i grafici e gli elo
        update_graph(new_meta.tour_id)
        #redirect alla pagina del torneo appena creato
        return redirect('/tournament/' + str(new_meta.tour_id))

def modify_tournament(request, id):

    #inizializzo il messaggio
    success = ''

    #se POST
    if request.method == 'POST':
        
        if request.POST.get('save'):
            #aggiorno il torneo
            success = modify_tour(request.POST.copy())
            id = int(request.POST.get('save'))
            #rifaccio elo e grafici
            thread = Thread(
                target=update_graph,
                args=(id,)
            )
            thread.start()

        elif request.POST.get('delete'):

            #elimino il torneo
            delete_tour(id)
            #rifaccio i grafici
            update_graph()
            #redirect alla pagina dei tornei
            return render(request, "main/tournament_deleted.html")




    meta, matches, min_date, warning = get_tour(id)
    context = {
        'id': id,
        'success': success,
        'warning': warning,
        'meta': meta,
        'matches': matches,
        'min_date': min_date
    }
    return render(request, "main/tournament.html", context=context)

def manage_tournaments(request):

    if request.method == 'GET':
        #recupero i tornei ordinati per data
        tours = tournaments_by_date()
        context = {
            'tours': tours
        }
    else:
        #prendo il torneo
        tour_id = int(request.POST.get('tour_id'))
        #redirect alla pagina del torneo
        return redirect('/tournament/' + str(tour_id))


    return render(request, "main/manage_tournaments.html", context)
