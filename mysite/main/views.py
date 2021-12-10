from django.shortcuts import render, redirect
from django.urls import reverse
import os
from elolib import fill_elo, reset_elo, generate_tour_table, \
    save_tour,  get_tour,  modify_tour, pivot_elo,  update_graph, \
    tournaments_by_date, delete_tour, get_leaderboard

# Create your views here.
def index(request):
    #controllo, se non esiste il grafico lo creo
    if not os.path.isfile('mysite/main/templates/graphs/elo_graph.html'):
        update_graph()
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
            fill_elo()
            pass

    context = pivot_elo()

    return render(request, "main/elo_table.html", context=context)

def new_tournament(request):

    #se GET
    if request.method == 'GET':

        context = generate_tour_table(request.GET.copy())

        return render(request, "main/new_tournament.html", context=context)

    #se POST
    if request.method == 'POST':
        
        #i dati inseriti sono già validi grazie all'html
        new_meta = save_tour(request.POST.copy())
        #aggiorno i grafici e gli elo
        update_graph()
        #redirect alla pagina del torneo appena creato
        return redirect('modify_tournament', new_meta.tour_id)

def modify_tournament(request, id):

    #inizializzo il context
    context = {
        'id': id,
        'success': ''
    }

    #se POST
    if request.method == 'POST':
        
        if request.POST.get('save'):
            #aggiorno il torneo
            context['success'] = modify_tour(request.POST.copy())
            #rifaccio elo e grafici
            update_graph()

        elif request.POST.get('delete'):

            #elimino il torneo
            delete_tour(id)
            #rifaccio i grafici
            update_graph()
            #redirect alla pagina dei tornei
            return render(request, "main/tournament_deleted.html")

        elif request.POST.get('previous'):
            #redirect alla pagina del torneo precedente
            return redirect('modify_tournament', request.POST.get('previous'))

        elif request.POST.get('next'):
            #redirect alla pagina del torneo successivo
            return redirect('modify_tournament', request.POST.get('next'))

    #aggiungo i dati 
    context = {**context, **get_tour(id)} 

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
        return redirect('modify_tournament', tour_id)


    return render(request, "main/manage_tournaments.html", context)


def leaderboard(request):

    context = get_leaderboard()

    return render(request, "main/leaderboard.html", context=context)
