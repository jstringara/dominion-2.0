from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import now
import json

# Create your models here.
class Metadata(models.Model):

    date = models.DateTimeField(default=now)
    N = models.IntegerField()
    tour_id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.date.strftime('%a %d-%m-%y (%H:%M)')

class Championship(models.Model):

    champ_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    participants = models.CharField(default='[]',max_length=200)
    tours = models.CharField(default='[]',max_length=255)
    is_active = models.BooleanField(default=False)

    def set_active(self)->None:
        '''
        Metodo che attiva il campionato, disattivando tutti gli altri.
        Se già attivo ritorna un'eccezione.
        '''
        #verifico che sia inattivo
        if self.is_active:
            raise Exception('Campionato già attivo')
        #disattivo tutti i campionati
        Championship.objects.filter(is_active=True).update(is_active=False)
        #attivo il campionato
        self.is_active = True
        self.save()

    def get_participants(self)->list[int]:
        '''
        Metodo che ritorna una lista di id id utenti
        partecipanti al campionato.
        '''
        #parse del testo come json
        participants = json.loads(self.participants)
        #trasformo in lista di utenti
        return participants

    def get_users(self)->list[User]:
        '''
        Metodo che ritorna una lista di oggetti User
        partecipanti al campionato.
        '''
        #parse del testo come json
        participants = json.loads(self.participants)
        #trasformo in lista di utenti
        return [User.objects.get(id=p) for p in participants]

    def is_participant(self , player:User)->bool:
        '''
        Metodo che preso un oggetto User, verifica se è partecipante
        '''
        #verifico che sia un id valido
        partecipants = self.get_participants()
        return player.id in partecipants

    def add_participant(self, new_p:User)->None:
        '''
        Metodo che dato un id aggiunge l'utente al campionato.
        Se l'utente non esiste o partecipa già ritorna un'eccezione.
        '''
        #verifico che non sia già partecipante
        if self.is_participant(new_p):
            raise Exception('Utente già partecipante')
        #aggiungo l'utente
        participants = self.get_participants()
        participants.append(new_p.id)
        self.participants = json.dumps(participants)
        self.save()

    def remove_participant(self, new_p:User)->None:
        '''
        Metodo che dato un id rimuove l'utente dal campionato.
        Se l'utente non esiste o non partecipa ritorna un'eccezione.
        '''
        #verifico che sia partecipante
        if not self.is_participant(new_p):
            raise Exception('Utente non partecipante')
        #rimuovo l'utente
        participants = self.get_participants()
        participants.remove(new_p.id)
        self.participants = json.dumps(participants)
        self.save()

    def get_tours(self) -> list[int]:
        '''
        Metodo che ritorna una lista di id di tornei
        rappresentanti i turni del campionato.
        '''
        #parse del testo come json
        tours = json.loads(self.tours)
        #trasformo in lista di oggetti
        return tours

    def get_metadata(self)->list[Metadata]:
        '''
        Metodo che ritorna una lista di oggetti Metadata
        rappresentanti i turni del campionato.
        '''
        #parse del testo come json
        tours = json.loads(self.tours)
        #trasformo in lista di oggetti
        return [Metadata.objects.get(id=t) for t in tours]

    def is_tour(self, tour:Metadata)->bool:
        '''
        Metodo che dato un oggetto Metadata verifica se è un turno
        del campionato.
        '''
        tours = self.get_tours()
        return tour in tours

    def add_tour(self, new_t:Metadata)->None:
        '''
        Metodo che dato un oggetto Metadata aggiunge il turno al campionato.
        Se il turno c'è già ritorna un'eccezione.
        '''
        #verifico che il turno non sia già presente
        if self.is_tour(new_t):
            raise Exception('Turno già presente')
        #aggiungo il turno
        tours = self.get_tours()
        tours.append(new_t.id)
        self.tours = json.dumps(tours)
        self.save()

    def remove_tour(self, new_t:Metadata)->None:
        '''
        Metodo che dato un oggetto Metadata rimuove il turno dal campionato.
        Se il turno non è presente ritorna un'eccezione.
        '''
        #verifico che il turno sia presente
        if not self.is_tour(new_t):
            raise Exception('Turno non presente')
        #rimuovo il turno
        tours = self.get_tours()
        tours.remove(new_t.id)
        self.tours = json.dumps(tours)
        self.save()

    def __str__(self):
        return self.name

class Game(models.Model):

    player_id_1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='player_id_1')
    points_1 = models.IntegerField(null=True, blank=True)
    turns_1 = models.IntegerField(null=True, blank=True)
    player_id_2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='player_id_2')
    points_2 = models.IntegerField(null=True, blank=True)
    turns_2 = models.IntegerField(null=True, blank=True)
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

    def outcome(self):
        outcome_1 = (self.points_1 > self.points_2)+\
            (self.points_1 == self.points_2)*(self.turns_1 < self.turns_2)+\
            0.5*(self.points_1 == self.points_2)*(self.turns_1 == self.turns_2)
        outcome_2 = 1-outcome_1
        return [
            (self.player_id_1, outcome_1),
            (self.player_id_2, outcome_2)
        ]

    def __str__(self):
        return str(self.player_id_1)+', '+str(self.player_id_2)+', '+str(self.tour_id)

class Constant(models.Model):
    k = models.IntegerField(default=20)

class Elo(models.Model):

    player_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    elo = models.FloatField(default=1500)
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.player_id)+', '+str(self.tour_id)

class Albo(models.Model):

    player_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    number = models.IntegerField()
    tour_id = models.ForeignKey(Metadata, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.player_id)+', Campione '+str(self.number)+'/'+str(self.number)

