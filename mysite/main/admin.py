from django.contrib import admin
from .models import Metadata, Game, Constant

# Register your models here.
admin.site.register(Metadata)
admin.site.register(Game)
admin.site.register(Constant)
