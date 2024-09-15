from main.models import Parameter, EloScore, Match, Result, Tournament, Season
from django.contrib.auth.models import User
from django.contrib import messages
import pandas as pd
import numpy as np
import os
import json
from random import shuffle, sample
from plotly.express import line
from datetime import timedelta, datetime
from itertools import combinations
from zoneinfo import ZoneInfo
from elo_math import get_expected_score, get_updated_rating

with open("config.json", "r") as f:
    config = json.load(f)


# funzione per trasformare una stringa in int o None
def to_int(string):
    try:
        return int(string)
    except ValueError:
        return None


def calculate_match_outcome(
    num_points_current, num_turns_current, num_points_opponent, num_turns_opponent
):
    """
    Function that calculates the outcome of a match for the current player against
    the opponent player.
    """

    # case in which the game is not finished
    if num_points_current is None and num_points_opponent is None:
        return 0

    if num_points_current > num_points_opponent:
        return 1
    elif num_points_current < num_points_opponent:
        return 0
    elif num_turns_current < num_turns_opponent:
        return 1
    elif num_turns_current > num_turns_opponent:
        return 0
    else:
        return 0.5


# TODO this has to be refactored
def p(x, X, y, Y):
    """
    Funzione che calcola la percentuale di x in x+y
    anche per numeri negativi.
    Se entrambi 0 si appoggia ai turni.
    """
    # se uno di questi è None ritorno 0
    if x is None or y is None:
        return 0
    # se entrambi sono 0 e i turni sono definiti torno l'esito
    if x == 0 and y == 0 and X is not None and Y is not None:
        return calculate_match_outcome(x, X, y, Y)
    # somma positiva
    if x + y > 0:
        return int(100 * x / (x + y))
    # somma negativa
    if x + y < 0:
        return int(100 * (1 - x / (x + y)))
    # se a somma 0
    if x + y == 0:
        # se entrambi 0
        if x == 0 and y == 0:
            return 0
        # se complementari
        elif x > 0:
            return 200
        elif x < 0:
            return -100


def get_player_elo_at_tournament(player, tournament):
    """
    Funzione che restituisce l'Elo score di un giocatore al momento di un torneo.
    """

    # get the Elo score of the player at the time of the tournament
    elo = (
        EloScore.objects.filter(player=player, tournament__datetime__lte=tournament.datetime)
        .order_by("-tournament__datetime")
        .first()
    )

    return elo.elo if elo else 0


def fill_elo(season, start_date):
    """
    Fill the EloScore table with the Elo scores of the players.

    Parameters:
    season (Season): the season for which to fill the Elo scores
    start_date (datetime): the date from which to start filling the Elo scores

    The procedure stops if it encounters a match with incomplete results.
    """

    # As a first step, I delete all the Elo scores that have been computed after the start_date in the season
    EloScore.objects.filter(
        tournament__datetime__gte=start_date,
        tournament__season=season,
    ).delete()

    # Now I loop through all the tournaments in the season that have been held after the start_date
    tournaments = Tournament.objects.filter(
        datetime__gte=start_date,
        season=season,
    ).order_by("datetime")

    for tournament in tournaments:
        matches = Match.objects.filter(tournament=tournament)
        players = set(Result.objects.filter(match__in=matches).values_list("player", flat=True))

        # Check if there are any matches with incomplete results
        if any(
            result.num_points is None or result.num_turns is None
            for result in Result.objects.filter(match__in=matches)
        ):
            return

        # Get the previous tournament
        prev_tournament = (
            Tournament.objects.filter(datetime__lt=tournament.datetime, season=season)
            .order_by("-datetime")
            .first()
        )

        # Get the initial Elo ratings for the players
        initial_elos = {
            player: get_player_elo_at_tournament(player, prev_tournament) for player in players
        }

        # Calculate the expected scores
        expected_scores = {player: 0 for player in players}
        for player in players:
            for opponent in players:
                if player != opponent:
                    expected_scores[player] += get_expected_score(
                        initial_elos[player], initial_elos[opponent]
                    )

        # Calculate the actual scores
        actual_scores = {player: 0 for player in players}
        for match in matches:
            results = Result.objects.filter(match=match)
            if len(results) == 2:
                player1, player2 = results[0].player, results[1].player
                score1 = calculate_match_outcome(
                    results[0].num_points,
                    results[0].num_turns,
                    results[1].num_points,
                    results[1].num_turns,
                )
                score2 = 1 - score1
                actual_scores[player1] += score1
                actual_scores[player2] += score2

        # Get the total number of players
        n = User.objects.filter(is_staff=False).count()

        # Calculate the K factor
        k = Parameter.objects.first().k * len(players) / n

        new_elos = {}
        for player in players:
            new_elos[player] = get_updated_rating(
                initial_elos[player], expected_scores[player], actual_scores[player], k
            )
            EloScore.objects.create(player=player, tournament=tournament, elo=new_elos[player])


# TODO this has to be refactored
def new_tour():
    """
    Funzione che crea un nuovo torneo
    """
    # prendo i player
    players = User.objects.filter(is_staff=False)

    return {"players": players}


# TODO this has to be refactored
def save_tour(post_data):
    # tolgo il token
    post_data.pop("csrfmiddlewaretoken")
    # assegno a variabili comode
    num_players = to_int(post_data.pop("player_num")[0])
    # genero le stringhe per i player
    players = User.objects.filter(is_staff=False)
    # estraggo e metto in int
    presences = {p: to_int(post_data.pop("p_" + str(p.id))[0]) for p in players}

    # sommo controllando che siano solo 1 o 0
    sum_presences = 0
    for p in presences.values():
        if p not in [0, 1]:
            return {"warning": "Hai inserito un valore non valido", "players": players}
        sum_presences += p

    # controllo che i numeri combacino e siano non zero
    if sum_presences != num_players and num_players <= 0:
        return {
            "warning": "Hai inserito un numero di giocatori non valido",
            "players": players,
        }

    # prendo la data e l'orario di adesso
    tour_date = datetime.now(tz=ZoneInfo("Europe/Rome"))

    # if there already exists a tournament with such date, return a warning
    if Tournament.objects.filter(datetime=tour_date).exists():
        return {"warning": "Esiste già un torneo con questa data", "players": players}

    # prendo i giocatori presenti
    players = [p for p in presences if presences[p] == 1]
    # genero tutte le combinazioni
    combos = list(combinations(players, 2))
    # rendo liste e mischio
    combos = [sample(list(c), 2) for c in combos]
    # mischio la lista
    shuffle(combos)

    # get the current season, i.e. the object among the Season objects whose is_current field is True
    current_season = Season.objects.get(is_current=True)

    # create the tournament
    tournament = Tournament.objects.create(season=current_season, datetime=tour_date)

    # create the matches
    for combo in combos:
        match = Match.objects.create(tournament=tournament)

        Result.objects.create(
            match=match,
            player=combo[0],
            num_turns=None,
            num_points=None,
        )

        Result.objects.create(
            match=match,
            player=combo[1],
            num_turns=None,
            num_points=None,
        )

    return {"tournament": tournament}


def get_tour(tournament: Tournament):
    """
    Funzione che restituisce i dati di un torneo dal suo id.
    """

    warning = ""

    # if the tournament does not exist raise a pop up and redirect to the manage tournaments page
    if not Tournament.objects.filter(id=tournament.id).exists():
        warning = f"Il torneo con ID {tournament.id} non esiste"
        return {"warning": warning}

    results = Result.objects.filter(match__tournament=tournament)
    print(results)
    match_data = {}
    for result in results:
        match_id = result.match.id
        if match_id not in match_data:
            match_data[match_id] = {}
        if "player_id_1" not in match_data[match_id]:
            match_data[match_id]["player_id_1"] = result.player.id
            match_data[match_id]["player_id_1__username"] = result.player.username
            match_data[match_id]["points_1"] = result.num_points
            match_data[match_id]["turns_1"] = result.num_turns
        else:
            match_data[match_id]["player_id_2"] = result.player.id
            match_data[match_id]["player_id_2__username"] = result.player.username
            match_data[match_id]["points_2"] = result.num_points
            match_data[match_id]["turns_2"] = result.num_turns

    matches = pd.DataFrame(match_data.values())

    # Trasformo in dataframe
    # cols = [
    #     "player_id_1",
    #     "player_id_1__username",
    #     "points_1",
    #     "turns_1",
    #     "player_id_2",
    #     "player_id_2__username",
    #     "points_2",
    #     "turns_2",
    # ]
    # matches = pd.DataFrame(matches.values_list(*cols), columns=cols)
    # creo la colonna 'outcome_1'
    matches["outcome_1"] = matches.apply(
        lambda x: calculate_match_outcome(x.points_1, x.turns_1, x.points_2, x.turns_2),
        axis=1,
    )
    matches["outcome_2"] = matches.apply(
        lambda x: calculate_match_outcome(x.points_2, x.turns_2, x.points_1, x.turns_1),
        axis=1,
    )
    # creo la colonna 'percent_1' delle percentuali
    matches["percent_1"] = matches.apply(
        lambda x: p(x.points_1, x.turns_1, x.points_2, x.turns_2), axis=1
    )
    matches["percent_2"] = matches.apply(
        lambda x: p(x.points_2, x.turns_2, x.points_1, x.turns_1), axis=1
    )

    # creo i totali
    totals = pd.DataFrame()
    totals["player_id"] = pd.concat([matches["player_id_1"], matches["player_id_2"]])
    totals["username"] = pd.concat(
        [matches["player_id_1__username"], matches["player_id_2__username"]]
    )
    totals["outcome"] = pd.concat([matches["outcome_1"], matches["outcome_2"]])
    totals["points"] = pd.concat([matches["points_1"], matches["points_2"]])
    totals["percent"] = pd.concat([matches["percent_1"], matches["percent_2"]])
    # converto i None in Nan
    totals = totals.fillna(value=np.nan)
    # sommo per id
    totals = totals.groupby(["player_id", "username"], dropna=False).sum().reset_index()
    # casto i punti ad interi
    totals = totals.astype({"points": int})
    # ordino per outcome
    totals = totals.sort_values(by=["outcome", "percent"], ascending=[False, False])

    tour_before = (
        Tournament.objects.filter(datetime__lt=tournament.datetime).order_by("-datetime").first()
        or None
    )

    tour_after = (
        Tournament.objects.filter(datetime__gt=tournament.datetime).order_by("datetime").first()
        or None
    )

    return {
        "tournament": tournament,
        "matches": matches.replace(np.nan, pd.NA).where(matches.notnull(), None),
        "totals": totals,
        "tour_before": tour_before,
        "tour_after": tour_after,
    }


# TODO this has to be refactored
def modify_tour(request):
    """
    Funzione che modifica un torneo.
    """

    data = request.POST.copy()
    # mi libero del token
    data.pop("csrfmiddlewaretoken")

    # inizializzo il success
    success = None

    # prendo l'id del torneo
    tour_id = int(data.pop("save")[0])
    # prendo i metadata corrispondenti
    meta = Tournament.objects.get(tour_id=tour_id)

    # prendo quella del post
    tour_date = datetime.strptime(data.pop("date")[0], "%Y-%m-%d")

    # se la data è diversa da quella del torneo
    if tour_date.date() != meta.date.date():
        # prendo il metadata con stessa data e ora più recente
        old_meta = (
            Tournament.objects.filter(date__date=tour_date.date()).order_by("-date__time").first()
        )
        # se esiste
        if old_meta:
            # aggiungo il tempo già passato più 1 ora
            tour_date = tour_date + timedelta(hours=old_meta.date.hour) + timedelta(hours=1)

        # aggiorno i metadati
        meta.date = tour_date
        meta.save()
        # salvo il success
        success = "Data modificata con successo"

    # definisco le colonne
    cols = ["player_id_1", "points_1", "turns_1", "player_id_2", "points_2", "turns_2"]

    # prendo le partite del torneo
    matches = Match.objects.filter(tour_id=tour_id)

    # genero le stringhe
    n = int(meta.N * (meta.N - 1) / 2)
    match_strings = ["M" + str(x) for x in range(1, n + 1)]

    # zippo insieme (hanno per forza lo stesso ordine)
    for string, match_tuple, match in zip(match_strings, matches.values_list(*cols), matches):
        # prendo l'id del giocatore 1
        player_id_1 = int(data[string + "_player1"])
        # prendo i punti 1
        points_1 = to_int(data[string + "_points1"])
        # prendo i turni 1
        turns_1 = to_int(data[string + "_turns1"])

        # prendo l'id del giocatore 2
        player_id_2 = int(data[string + "_player2"])
        # prendo i punti 2
        points_2 = to_int(data[string + "_points2"])
        # prendo i turni 2
        turns_2 = to_int(data[string + "_turns2"])

        # raccolgo
        entry = (player_id_1, points_1, turns_1, player_id_2, points_2, turns_2)

        # confronto i dati, se uguali salto
        if entry == match_tuple:
            continue

        # aggiorno i dati se non vuoti (cioè None, importante usare is not)
        if entry[1] is not None:
            match.points_1 = entry[1]
        if entry[2] is not None:
            match.turns_1 = entry[2]
        if entry[4] is not None:
            match.points_2 = entry[4]
        if entry[5] is not None:
            match.turns_2 = entry[5]
        # salvo il match
        match.save()

        success = "Modifica effettuata con successo"

    # aggiungo il success ai messaggi
    messages.success(request, success)


# TODO this has to be refactored
def delete_tour(id):
    """
    Funzione che elimina un torneo.
    """

    # Get the tournament that has to be deleted
    tournament = Tournament.objects.get(id=id)

    # Some elos are invalidated, so I have to delete them and recompute them
    elos = EloScore.objects.filter(tournament__datetime__gte=tournament.datetime)

    # elimino
    elos.delete()
    tournament.delete()


def pivot_elo(selected_season):
    elo = EloScore.objects.filter(
        tournament__season=selected_season,
    ).values_list(
        "tournament__datetime",
        "player__username",
        "elo",
    )

    if not elo:
        return {"df": pd.DataFrame()}

    elo = pd.DataFrame.from_records(elo, columns=["datetime", "name", "elo"])
    elo["elo"] = elo["elo"].astype(int)
    elo["datetime"] = elo["datetime"].dt.strftime("%Y-%m-%d %H:%M (%a)")
    elo = elo.pivot(index="datetime", columns="name", values="elo")
    elo = elo.reset_index()
    elo = elo.rename({"datetime": "Data e ora del torneo"}, axis=1)
    elo.columns.name = None
    context = {"df": elo}
    return context


def update_graph():
    # riempio l'elo
    # fill_elo() TODO

    # li prendo come dataframe
    df = pd.DataFrame.from_records(
        EloScore.objects.all().values_list(
            "tournament__datetime",
            "player__username",
            "elo",
            "tournament__season__name",
        ),
        columns=["Data", "Giocatore", "Elo", "Stagione"],
    )

    # Create a dropdown to choose the season
    seasons = df["Stagione"].unique()
    dropdown_buttons = [
        {
            "label": season,
            "method": "update",
            "args": [
                {"visible": df["Stagione"] == season},
                {"title": f"Grafico Elo - {season}"},
            ],
        }
        for season in seasons
    ]

    # Plot
    fig = line(
        df,
        x="Data",
        y="Elo",
        color="Giocatore",
        title="Grafico Elo",
        template="plotly_dark",
        line_shape="spline",
        markers=True,
    )

    # Add dropdown to the plot
    fig.update_layout(
        updatemenus=[
            {
                "buttons": dropdown_buttons,
                "direction": "down",
                "showactive": True,
            }
        ]
    )
    #
    # path
    graph_path = config["GRAPH_PATH"]
    # se non esiste la directory la creo
    if not os.path.exists(os.path.dirname(graph_path)):
        os.makedirs(os.path.dirname(graph_path))

    # salvo il grafico
    fig.write_html(file=graph_path, include_plotlyjs="cdn", include_mathjax=False, full_html=False)


def serve_graph():
    # apro il grafico
    with open(config["GRAPH_PATH"], "r") as f:
        return {"graph_code": f.read()}


def tournaments_by_date():
    tournaments = list(
        Tournament.objects.order_by("-datetime").values_list("datetime", "id", "season__name")
    )

    # scorro e ritorno tutti tranne il primo
    # (cioè l'ultimo in quest'ordine)
    return [
        {
            "datetime": tournament[0].strftime("%Y-%m-%d %H:%M"),
            "id": tournament[1],
            "season_name": tournament[2],
        }
        for tournament in tournaments
    ]


def get_leaderboard(selected_season):
    # take the last tournament where all Results are filled
    # TODO what happens if a tournament held on day T if not filled, but a tournament held on day T+1 is filled?
    last_tournament = (
        Tournament.objects.filter(
            season=selected_season,
            match__result__num_points__isnull=False,
            match__result__num_turns__isnull=False,
        )
        .order_by("-datetime")
        .first()
    )

    # take the palyer and elo from the last tournament
    last_elos = EloScore.objects.filter(tournament=last_tournament).values_list(
        "player__username", "elo"
    )

    # sort by elo
    last_elos = sorted(list(last_elos), key=lambda x: x[1], reverse=True)

    return {"elos": last_elos}


# TODO this has to be refactored
def get_variations():
    # prendo gli elo con data, nome ed elo
    context = pivot_elo()

    df = pd.DataFrame(context["data"], columns=context["header"])

    # prendo le colonne su cui fare i conti
    cols = context["header"][1:]

    # faccio la differenza, escludo la prima e ricasto ad int
    df[cols] = df[cols].diff()
    df = df[1:]
    # arrotondo
    df[cols] = df[cols].round(1)

    # creo i dataframe booleani di mvp e mongo
    mvp_df = df[cols].isin(df[cols].max(axis=1))
    mongo_df = df[cols].isin(df[cols].min(axis=1))

    # prendo le somme
    mvps = mvp_df.sum(axis=0)[cols]
    mongos = mongo_df.sum(axis=0)[cols]

    # prendo i nomi riga per riga
    df["MVP"] = mvp_df.apply(lambda x: ", ".join([cols[i] for i in range(len(x)) if x[i]]), axis=1)
    df["Mongo"] = mongo_df.apply(
        lambda x: ", ".join([cols[i] for i in range(len(x)) if x[i]]), axis=1
    )

    # trovo massimi e minimi globali
    max_mvp = df[cols].max().max()
    min_mong = df[cols].min().min()
    # trovo i nomi corrispondenti
    max_mvp_name = df[cols].max().idxmax()
    min_mong_name = df[cols].min().idxmin()
    # prendo header e data
    header = list(df.columns)
    data = list(zip(*map(df.get, df)))

    return {
        "header": header,
        "mvps": mvps,
        "mongos": mongos,
        "data": data,
        "max_mvp": max_mvp,
        "min_mong": min_mong,
        "max_mvp_name": max_mvp_name,
        "min_mong_name": min_mong_name,
    }


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


def get_tour_ajax(id):
    tour = get_tour(id)

    if tour["warning"]:
        return tour

    # prendo la data
    date = tour["meta"].date.strftime("%Y-%m-%d")

    # creo l'array
    array = [[[t[1], t[3], t[4]], [t[5], t[7], t[8]]] for t in tour["matches"].itertuples()]
    # flattening
    array = sum(array, [])
    # trasformo in stringhe
    array = [[str(int(x)) if x is not None else "" for x in t] for t in array]

    # creo l'array degli award e nomi
    awards = [[[t[2], t[9]], [t[6], t[10]]] for t in tour["matches"].itertuples()]
    # flattening
    awards = sum(awards, [])
    # casto solo il secondo a bool
    awards = [[t[0], bool(t[1])] for t in awards]

    # creo l'array dei totals
    totals = [[t[2], str(int(t[5])) + "%", str(t[3])] for t in tour["totals"].itertuples()]

    # ritorno
    return {
        "warning": tour["warning"],
        "date": date,
        "array": array,
        "awards": awards,
        "totals": totals,
    }


def update_tour_ajax(request, id):
    """
    Funzione che modifica un torneo.
    """

    data = request.POST.copy()
    # mi libero del token
    data.pop("csrfmiddlewaretoken")

    # prendo l'id del torneo
    tour_id = id
    # prendo i metadata corrispondenti
    meta = Tournament.objects.get(tour_id=tour_id)

    # prendo quella del post
    tour_date = datetime.strptime(data.pop("date")[0], "%Y-%m-%d")

    # se la data è diversa da quella del torneo
    if tour_date.date() != meta.date.date():
        # prendo il metadata con stessa data e ora più recente
        old_meta = (
            Tournament.objects.filter(date__date=tour_date.date()).order_by("-date__time").first()
        )
        # se esiste
        if old_meta:
            # aggiungo il tempo già passato più 1 ora
            tour_date = tour_date + timedelta(hours=old_meta.date.hour) + timedelta(hours=1)

        # aggiorno i metadati
        meta.date = tour_date
        meta.save()

    # definisco le colonne
    cols = ["player_id_1", "points_1", "turns_1", "player_id_2", "points_2", "turns_2"]

    # prendo le partite del torneo
    matches = Match.objects.filter(tour_id=tour_id)

    # prendo l'array delle partite
    array = json.loads(data.pop("array")[0])
    # lo accoppio a due a due
    array = [x + y for x, y in zip(array[::2], array[1::2])]

    # zippo insieme (hanno per forza lo stesso ordine)
    for array_row, match_tuple, match in zip(array, matches.values_list(*cols), matches):
        # prendo l'id del giocatore 1
        player_id_1 = int(array_row[0])
        # prendo i punti 1
        points_1 = to_int(array_row[1])
        # prendo i turni 1
        turns_1 = to_int(array_row[2])

        # prendo l'id del giocatore 2
        player_id_2 = int(array_row[3])
        # prendo i punti 2
        points_2 = to_int(array_row[4])
        # prendo i turni 2
        turns_2 = to_int(array_row[5])

        # raccolgo
        entry = (player_id_1, points_1, turns_1, player_id_2, points_2, turns_2)

        # confronto i dati, se uguali salto
        if entry == match_tuple:
            continue

        # aggiorno i dati se non vuoti (cioè None, importante usare is not)
        if entry[1] is not None:
            match.points_1 = entry[1]
        if entry[2] is not None:
            match.turns_1 = entry[2]
        if entry[4] is not None:
            match.points_2 = entry[4]
        if entry[5] is not None:
            match.turns_2 = entry[5]
        # salvo il match
        match.save()

    return "Modifiche salvate con successo"


def get_wins():
    tournaments = Tournament.objects.filter(
        match__result__num_points__isnull=False,
        match__result__num_turns__isnull=False,
    ).order_by("-datetime")

    # Initialize an empty list to store the data for each tournament
    data = []

    # Get all players
    players = User.objects.filter(is_staff=False)

    # Iterate over each tournament
    for tournament in tournaments:
        # Initialize a dictionary to store the results for the current tournament
        tournament_data = {"datetime": tournament.datetime, "disputed": 0}

        # Initialize player columns with "-"
        for player in players:
            tournament_data[player.username] = "-"

        # Get all matches for the current tournament
        matches = Match.objects.filter(tournament=tournament)

        # Iterate over each match
        for the_match in matches:
            # Get results for the match
            results = Result.objects.filter(match=the_match)

            if len(results) == 2:
                player1_result = results[0]
                player2_result = results[1]

                # Calculate match outcome
                outcome1 = calculate_match_outcome(
                    player1_result.num_points,
                    player1_result.num_turns,
                    player2_result.num_points,
                    player2_result.num_turns,
                )

                outcome2 = calculate_match_outcome(
                    player2_result.num_points,
                    player2_result.num_turns,
                    player1_result.num_points,
                    player1_result.num_turns,
                )

                # Update the number of disputed matches
                tournament_data["disputed"] += 1

                # Update the number of matches won by each player
                if tournament_data[player1_result.player.username] == "-":
                    tournament_data[player1_result.player.username] = 0
                if tournament_data[player2_result.player.username] == "-":
                    tournament_data[player2_result.player.username] = 0

                tournament_data[player1_result.player.username] += outcome1
                tournament_data[player2_result.player.username] += outcome2

        # Append the tournament data to the list
        data.append(tournament_data)

    # Create a DataFrame from the data
    wins_df = pd.DataFrame(data).reset_index(drop=True)

    # Format the datetime as YYYY-MM-DD HH:MM
    wins_df["datetime"] = wins_df["datetime"].dt.strftime("%Y-%m-%d %H:%M")

    return {"df": wins_df}


def get_n_out_of_n_champion(n: int):
    tournaments = Tournament.objects.all()
    champions = []

    for tournament in tournaments:
        results = Result.objects.filter(match__tournament=tournament)
        players = results.values_list("player", flat=True).distinct()

        for player in players:
            player_results = results.filter(player=player)
            wins = 0

            for result in player_results:
                opponent_results = results.filter(match=result.match).exclude(player=player)
                if opponent_results.exists():
                    opponent_result = opponent_results.first()
                    outcome = calculate_match_outcome(
                        result.num_points,
                        result.num_turns,
                        opponent_result.num_points,
                        opponent_result.num_turns,
                    )
                    # TODO what is the outcome is a draw, i.e. 0.5?
                    if outcome == 1:  # Assuming 1 indicates a win for the current player
                        wins += 1

            if wins == n and player_results.count() == n:
                champions.append(
                    {
                        "player": User.objects.get(id=player).username,
                        "datetime": tournament.datetime,
                        # "wins": wins,
                    }
                )

    df_champions = pd.DataFrame(champions)
    # format the datetime as YYYY-MM-DD HH:MM
    df_champions["datetime"] = df_champions["datetime"].dt.strftime("%Y-%m-%d %H:%M")

    return df_champions


# TODO this has to be refactored
def get_win_rates():
    # prendo le vittorie
    dict = get_wins()
    header = dict["header"][:-1]
    data = dict["data"]

    # creo i puntuali
    punt = [
        [row[0]]
        + [str(int(100 * x / row[-1])) + "%" if isinstance(x, float) else x for x in row[1:-1]]
        for row in data
    ]
    # inizializzo la prima riga
    data[0] = [
        data[0][0],
        *[(item, data[0][-1]) if isinstance(item, float) else ("-", "-") for item in data[0][1:-1]],
    ]
    # scorro i dati accopiati
    for i in range(1, len(data)):
        for j in range(1, len(data[i]) - 1):
            # se vuoto copio
            if data[i][j] == "-":
                data[i][j] = data[i - 1][j]
            else:  # se è un numero
                # se prima non ho niente, inizializzo
                if data[i - 1][j][0] == "-":
                    data[i][j] = (data[i][j], data[i][-1])
                # se prima ho un numero sommo
                else:
                    data[i][j] = (
                        data[i][j] + data[i - 1][j][0],
                        data[i][-1] + data[i - 1][j][1],
                    )
        data[i] = data[i][:-1]  # rimuovo la colonna delle disputate
    # calcolo le percentuali
    data = [
        [
            row[0],
            *[
                str(int(100 * x[0] / x[1])) + "%" if isinstance(x[0], float) else "-"
                for x in row[1:]
            ],
        ]
        for row in data
    ]

    return {"header": header, "punctual": punt, "cumulative": data}
