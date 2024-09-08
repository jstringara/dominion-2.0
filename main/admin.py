from django.contrib import admin

# from .models import Metadata, Game, EloOld
from .models import Parameter, Season, Tournament, Match, Result, EloScore

# Register your models here.
# admin.site.register(Metadata)
# admin.site.register(Game)
# admin.site.register(EloOld)
admin.site.register(Parameter)
admin.site.register(Season)
admin.site.register(Tournament)
admin.site.register(Match)
admin.site.register(Result)
admin.site.register(EloScore)
