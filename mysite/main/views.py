from django.shortcuts import render
from .models import Elo
import pandas as pd

# Create your views here.
def index(request):
    return render(request, "main/index.html")

def elo_table(request):

    #se post
    if request.method == 'POST':
        #se è stato premuto il bottone "Resetta Elo"
        if request.POST.get('reset_elo'):
           pass
        #se è stato premuto il bottone "Aggiorna Elo"
        if request.POST.get('update_elo'):
            #aggiorno gli elo
            pass

    #prendo gli elo con data, nome ed elo
    elo = Elo.objects.all().values_list('tour_id__date', 'player_id__username', 'elo')
    #creo il dataframe 
    elo = pd.DataFrame(list(elo), columns=['date', 'name', 'elo'])
    #faccio il pivot su date e la mantengo come colonna (.reset_index())
    elo = elo.pivot(index='date', columns='name', values='elo').reset_index()
    #formatto la data come giorno-mese
    elo['date'] = elo['date'].dt.strftime('%d-%m')
    #rinomino la colonna
    elo = elo.rename({'date': 'Data'}, axis=1)
    #arrotondo i punteggi
    elo = elo.round({col:0 for col in elo.columns[1::]})
    #casto a int
    for col in elo.columns[1::]:
        elo[col] = elo[col].astype(int)

    #prendo l'header della tabella
    header = list(elo.columns)
    #prendo i dati come lista di tuple (vedi https://stackoverflow.com/a/44350260/13373369)
    data = data = list(zip(*map(elo.get, elo)))
    #creo il context
    context = {'header': header, 'data': data}

    return render(request, "main/elo_table.html", context=context)
