from django.shortcuts import render, redirect
from django.http import JsonResponse
from main.models import Metadata
import os, json
from elolib import fill_elo, reset_elo, generate_tour_table, \
    save_tour,  get_tour,  modify_tour, pivot_elo,  update_graph, \
    tournaments_by_date, delete_tour, get_leaderboard, serve_graph,\
    get_variations, get_album, new_album_form, save_album, get_expected_score,\
    get_tour_ajax, update_tour_ajax, is_ajax

with open('config.json','r') as json_file:
    config = json.load(json_file)

# Create your views here.

#pagina home
def index(request):
    #controllo, se non esiste il grafico lo creo
    if not os.path.isfile(config["GRAPH_PATH"]):
        update_graph()
    context = serve_graph()
    return render(request, "main/index.html", context=context)

#tavola degli elo
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

#nuovo torneo
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

#torneo eliminato
def tournament_deleted(request):
    return render(request, "main/tournament_deleted.html")

#modifica torneo
def modify_tournament(request, id):

    #inizializzo il context
    context = {
        'id': id
    }

    #se POST
    if request.method == 'POST':
        
        if request.POST.get('save'):
            #aggiorno il torneo
            modify_tour(request)
            #rifaccio elo e grafici
            update_graph()
            #redirigo alla pagina del torneo
            return redirect('modify_tournament', id)

        elif request.POST.get('delete'):

            #elimino il torneo
            delete_tour(id)
            #rifaccio i grafici
            update_graph()
            #redirect alla pagina dei tornei
            return redirect('tournament_deleted')

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

def last_tournament(request):
    
    #recupero l'ultimo torneo
    last_id = Metadata.objects.order_by('-date').first().tour_id

    return redirect('modify_tournament', last_id)

def leaderboard(request):

    context = get_leaderboard()

    return render(request, "main/leaderboard.html", context=context)

def variations(request):

    context = get_variations()

    return render(request, "main/variations.html", context=context)

def album(request):

    context = get_album()

    return render(request, "main/album.html", context=context)

def new_album(request):

    #se GET
    if request.method == 'GET':

        context = new_album_form()

        return render(request, "main/new_album.html", context=context)

    if request.method == 'POST':

        #i dati inseriti sono già validi grazie all'html
        save_album(request.POST.copy())
        #aggiorno i grafici e gli elo
        return redirect('album')

def get_expected(request):

    #se GET
    context = get_expected_score(request.GET.copy())


    return render(request, "main/expected_scores.html", context)

def refresh_tour(request,id):

    #request should be ajax and method should be GET.
    if is_ajax(request) and request.method == "GET":
        try:
            tour = get_tour_ajax(id)
            return JsonResponse(tour, status=200)
        except: #nel caso ci sia un'eccezione (es. non esiste il torneo)
            return JsonResponse({"error": "Bad Request"}, status=400)
    else:
        # return bad request status code
        return JsonResponse({"error": "Bad Request"}, status=400)

def update_tour(request,id):

    #request should be ajax and method should be POST.
    if is_ajax(request) and request.method == "POST":

        try:
            #aggiorno il torneo
            msg = update_tour_ajax(request, id)
            #rifaccio elo e grafici
            update_graph()
            #ritorno il successo
            return JsonResponse({"success": msg}, status=200)
        except:  # nel caso ci sia un'eccezione (es. non esiste il torneo)
            return JsonResponse({"error": "Bad Request"}, status=400)
    else:
        # return bad request status code
        return JsonResponse({"error": "Bad Request"}, status=400)

def refresh_graph(request):
    if is_ajax(request) and request.method == "GET":
        return JsonResponse(serve_graph(), status=200)
    else:
        return JsonResponse({"error": "Bad Request"}, status=400)
