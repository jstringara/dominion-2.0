from django.contrib.auth.backends import UserModel
from django.core.management.base import BaseCommand
from main.models import Metadata, Game, Constant
from django.contrib.auth import get_user_model
import pandas as pd
import os
from datetime import datetime


class Command(BaseCommand):
    help = "Runs the database setup"

    def add_metadata(self):
        # carico il file metadata.csv
        df = pd.read_csv("Data/metadata.csv")
        z = [df[name].to_list() for name in df.columns[:-1]]

        def mkdate(date):
            format_str = "%Y-%m-%d"
            return datetime.strptime(date, format_str)

        meta = [(d, N) for d, N in zip(z[0], z[2])]
        meta.append((mkdate("2020-12-31"), 6))

        # inserisco nel database al contrario
        for d, N in meta[::-1]:
            Metadata.objects.create(date=d, N=N)

    def add_users(self):
        # carico il file users.csv
        df = pd.read_csv("Data/users.csv")
        z = [df[name].to_list() for name in df.columns]
        players = [(name, p) for name, p in zip(z[0], z[1])]

        # inserisco nel database
        for name, p in players:
            UserModel.objects.create_user(username=name, password=p)

    def add_games(self):
        # apro i file di users e metadata

        # prendo gli oggetti users da db e
        # li inserisco nel dict
        users = {u.username: u for u in UserModel.objects.all()}

        # prendo i tornei
        df = pd.read_csv("Data/metadata.csv")
        # dict {id_file: id_db}
        tours = {id: n for id, n in zip(df["ID"][::-1], range(2, len(df) + 2))}
        # trasformo in dict {id_file: oggetto_db}
        tours = {id: Metadata.objects.get(tour_id=n) for id, n in tours.items()}

        # inizializzo i matches
        matches = []

        # prendo i nomi dei file
        files = os.listdir("Data/Tournaments")
        for file in files:
            # apro il file
            df = pd.read_csv("Data/Tournaments/" + file)
            # prendo l'id
            id = file.split(".")[0]

            # raggruppo il torneo per partite
            z = df.groupby("ID")

            # per ogni partita
            for match in z:
                match = match[1]
                # prendo giocatori e punti
                players = [users[n] for n in match["Giocatore"]]
                points = [p for p in match["Punti"]]
                # prendo gli esiti per calcolare i turni
                out = [o for o in match["Esito"]]
                # calcolo i turni
                turns = [
                    1 + (points[0] == points[1]) * (o != 0.5) * (o == 0) for o in out
                ]

                # aggiungo il match
                matches.append(
                    (
                        players[0],
                        points[0],
                        turns[0],
                        players[1],
                        points[1],
                        turns[1],
                        tours[id],
                    )
                )

        # inserisco i match nel db
        for m in matches:
            Game.objects.create(
                player_id_1=m[0],
                points_1=m[1],
                turns_1=m[2],
                player_id_2=m[3],
                points_2=m[4],
                turns_2=m[5],
                tour_id=m[6],
            )

    def add_constant(self):
        # aggiungo la costante
        Constant.objects.create()

    def handle(self, *args, **options):
        # self.add_metadata()
        # self.add_users()
        # self.add_games()
        # self.add_constant()
        pass
