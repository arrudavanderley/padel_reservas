from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Bloqueo, Perfil, Pista, Reserva


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil'


class UsuarioAdmin(UserAdmin):
    """Reemplaza el admin de User por defecto para mostrar también el Perfil."""
    inlines = [PerfilInline]


# Sustituye el registro por defecto de User por la versión con el Perfil integrado.
admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)


@admin.register(Pista)
class PistaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'color', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre']


@admin.action(description='Cancelar las reservas seleccionadas')
def cancelar_reservas_seleccionadas(modeladmin, request, queryset):
    actualizadas = queryset.update(estado='cancelada')
    modeladmin.message_user(request, f'{actualizadas} reserva(s) cancelada(s).')


@admin.action(description='Confirmar las reservas seleccionadas')
def confirmar_reservas_seleccionadas(modeladmin, request, queryset):
    actualizadas = queryset.update(estado='confirmada')
    modeladmin.message_user(request, f'{actualizadas} reserva(s) confirmada(s).')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['pista', 'usuario', 'fecha', 'hora_inicio', 'hora_fin', 'estado', 'recurrente']
    list_filter = ['pista', 'estado', 'recurrente', 'fecha']
    search_fields = ['usuario__username', 'usuario__email', 'pista__nombre']
    date_hierarchy = 'fecha'
    actions = [cancelar_reservas_seleccionadas, confirmar_reservas_seleccionadas]


@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ['pista', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'motivo']
    list_filter = ['pista']
    date_hierarchy = 'fecha_inicio'
