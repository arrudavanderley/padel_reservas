from django.contrib import admin
from .models import Pista, Reserva, Bloqueo

@admin.register(Pista)
class PistaAdmin(admin.ModelAdmin):
    list_display = ('id','nombre','activa')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id','usuario','pista','fecha','hora_inicio','hora_fin','estado')
    list_filter = ('estado','pista','fecha')

@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ('pista','fecha_inicio','fecha_fin','motivo')
    
