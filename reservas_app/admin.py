from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group, User
from django.db.models import Count
from datetime import date, timedelta
from .models import Pista, Reserva, Bloqueo


@admin.register(Pista)
class PistaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'activa')
    actions = None

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Clic en la pista a modificar'
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'pista', 'fecha', 'hora_inicio', 'hora_fin', 'estado')
    list_filter = ('estado', 'pista', 'fecha')
    search_fields = ('usuario__username', 'usuario__email')
    actions = None

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Clic en la reserva a modificar'
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pista', 'fecha_inicio', 'fecha_fin', 'motivo')
    actions = None

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Clic en el bloqueo a modificar'
        return super().changelist_view(request, extra_context=extra_context)


admin.site.unregister(User)


@admin.register(User)
class UsuarioAdmin(DjangoUserAdmin):
    actions = None

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Clic en el usuario a modificar'
        return super().changelist_view(request, extra_context=extra_context)


admin.site.unregister(Group)


@admin.register(Group)
class GrupoAdmin(DjangoGroupAdmin):
    actions = None

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Clic en el grupo a modificar'
        return super().changelist_view(request, extra_context=extra_context)


_admin_index_original = admin.site.index


def _index_con_contexto(request, extra_context=None):
    hoy = date.today()
    extra_context = extra_context or {}
    extra_context.update({
        'hoy': hoy,
        'total_hoy': Reserva.objects.filter(fecha=hoy, estado='confirmada').count(),
        'total_mes': Reserva.objects.filter(fecha__gte=hoy.replace(day=1), estado='confirmada').count(),
        'por_pista': Reserva.objects.filter(fecha__gte=hoy - timedelta(days=30), estado='confirmada')
            .values('pista__nombre').annotate(total=Count('id')).order_by('-total'),
        'top_usuarios': Reserva.objects.filter(estado='confirmada')
            .values('usuario__username').annotate(total=Count('id')).order_by('-total')[:5],
        'pistas': Pista.objects.all(),
    })
    return _admin_index_original(request, extra_context)


admin.site.index = _index_con_contexto
