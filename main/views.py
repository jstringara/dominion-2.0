from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from main.models import Tournament
from .models import Season
import os
import json
from elolib import (
    fill_elo,
    reset_elo,
    get_tour,
    save_tour,
    new_tour,
    modify_tour,
    pivot_elo,
    update_graph,
    tournaments_by_date,
    delete_tour,
    get_leaderboard,
    serve_graph,
    get_variations,
    get_expected_score,
    get_tour_ajax,
    update_tour_ajax,
    is_ajax,
    get_wins,
    get_win_rates,
    get_n_out_of_n_champion,
)

with open("config.json", "r") as json_file:
    config = json.load(
        json_file
    )  # TODO move in a settings.py and load here with from django.conf import settings


def page_dependent_from_season(request, get_context: callable):
    seasons = Season.objects.all()
    selected_season_id = request.GET.get("season_id")
    if selected_season_id:
        selected_season = Season.objects.get(id=selected_season_id)
    else:
        selected_season = Season.objects.filter(is_current=True).first()

    context = get_context(selected_season)
    context["seasons"] = seasons
    context["selected_season"] = selected_season

    return context


# Create your views here.


def create_season(request):
    if request.method == "POST":
        name = request.POST.get("name")
        Season.objects.create(name=name)
        return redirect("season_management")
    return render(request, "main/create_season.html")


def season_action(request):
    if request.method == "POST":
        action = request.POST.get("action")
        season_id = request.POST.get("season_id")

        if action == "delete":
            return delete_season(request, season_id)
        elif action == "set_current":
            return select_current_season(request, season_id)

    return redirect("season_management")


def delete_season(request, season_id):
    season = get_object_or_404(Season, id=season_id)
    season.delete()
    return redirect("season_management")


def select_current_season(request, season_id):
    Season.objects.update(is_current=False)
    season = get_object_or_404(Season, id=season_id)
    season.is_current = True
    season.save()
    return redirect("season_management")


def season_management(request):
    seasons = Season.objects.all()
    return render(request, "main/season_management.html", {"seasons": seasons})


def index(request):
    # controllo, se non esiste il grafico lo creo
    # if not os.path.isfile(config["GRAPH_PATH"]): # TODO
    update_graph()
    context = serve_graph()
    return render(request, "main/index.html", context=context)


# tavola degli elo
def elo_table(request):
    context = page_dependent_from_season(request, pivot_elo)

    return render(request, "main/elo_table.html", context=context)


# region torneo
def new_tournament(request):
    # se GET
    if request.method == "GET":
        # context = generate_tour_table(request.GET.copy())
        context = new_tour()

        return render(request, "main/new_tournament.html", context=context)

    # se POST
    if request.method == "POST":
        context = save_tour(request.POST.copy())
        if context.get("warning"):
            return render(request, "main/new_tournament.html", context=context)

        return redirect("modify_tournament", context["tournament"].id)


# torneo eliminato
def tournament_deleted(request):
    return render(request, "main/tournament_deleted.html")


# modifica torneo
def modify_tournament(request, tournament_id: int):
    # inizializzo il context
    tournament = Tournament.objects.get(id=tournament_id)
    context = {"tournament": tournament}

    # se POST
    if request.method == "POST":
        if request.POST.get("save"):
            # aggiorno il torneo
            modify_tour(request)
            # rifaccio elo e grafici
            update_graph()
            # redirigo alla pagina del torneo
            return redirect("modify_tournament", tournament.id)

        elif request.POST.get("delete"):
            # elimino il torneo
            delete_tour(tournament.id)
            # rifaccio i grafici
            update_graph()
            # redirect alla pagina dei tornei
            return redirect("tournament_deleted")

    # aggiungo i dati
    context = {**context, **get_tour(tournament)}

    return render(request, "main/tournament.html", context=context)


def manage_tournaments(request):
    if request.method == "GET":
        # recupero i tornei ordinati per data
        tours = tournaments_by_date()
        context = {"tours": tours}
    else:
        # prendo il torneo
        tour_id = int(request.POST.get("tour_id"))
        # redirect alla pagina del torneo
        return redirect("modify_tournament", tour_id)

    return render(request, "main/manage_tournaments.html", context)


def last_tournament(request):
    # get the last tournament id
    last_id = Tournament.objects.order_by("datetime").last().id

    return redirect("modify_tournament", last_id)


# endregion


def leaderboard(request):
    context = page_dependent_from_season(request, get_leaderboard)
    return render(request, "main/leaderboard.html", context=context)


def variations(request):
    context = get_variations()

    return render(request, "main/variations.html", context=context)


def album(request):
    context = {
        "df_champions_3": get_n_out_of_n_champion(3),
        "df_champions_4": get_n_out_of_n_champion(4),
        "df_champions_5": get_n_out_of_n_champion(5),
    }

    return render(request, "main/album.html", context=context)


def get_expected(request):
    context = get_expected_score()

    return render(request, "main/expected_scores.html", context)


def wins(request):
    context = get_wins()
    return render(request, "main/wins.html", context=context)


def win_rates(request):
    context = get_win_rates()
    return render(request, "main/win_rates.html", context=context)


# region ajax
def refresh_tour(request, tournament_id):
    # request should be ajax and method should be GET.
    if is_ajax(request) and request.method == "GET":
        try:
            tour = get_tour_ajax(tournament_id)
            return JsonResponse(tour, status=200)
        except Exception as e:  # nel caso ci sia un'eccezione (es. non esiste il torneo)
            return JsonResponse({"error": str(e)}, status=400)
    else:
        # return bad request status code
        return JsonResponse({"error": "Bad Request"}, status=400)


def update_tour(request, tournament_id):
    # request should be ajax and method should be POST.
    if is_ajax(request) and request.method == "POST":
        try:
            # aggiorno il torneo
            msg = update_tour_ajax(request, tournament_id)
            # rifaccio elo e grafici
            update_graph()
            # ritorno il successo
            return JsonResponse({"success": msg}, status=200)
        except Exception as e:  # nel caso ci sia un'eccezione (es. non esiste il torneo)
            return JsonResponse({"error": str(e)}, status=400)
    else:
        # return bad request status code
        return JsonResponse({"error": "Bad Request"}, status=400)


def refresh_graph(request):
    if is_ajax(request) and request.method == "GET":
        return JsonResponse(serve_graph(), status=200)
    else:
        return JsonResponse({"error": "Bad Request"}, status=400)


def expected_ajax(request):
    if is_ajax(request) and request.method == "GET":
        context = get_expected_score()

        return JsonResponse(
            {
                "K": context.get("K"),
                "elos": {
                    user.id: {
                        "elo": elo.elo,
                        "check": "c_" + str(user.id),
                        "exp": "e_" + str(user.id),
                        "inp": str(user.id),
                        "nelo": "n_" + str(user.id),
                    }
                    for user, elo in zip(context.get("players"), context.get("elos"))
                },
            },
            status=200,
        )
    else:
        return JsonResponse({"error": "Bad Request"}, status=400)


def win_rates_ajax(request, kind):
    if is_ajax(request) and request.method == "GET":
        context = get_win_rates(kind).drop("header")
        return JsonResponse(context, status=200)
    else:
        return JsonResponse({"error": "Bad Request"}, status=400)
