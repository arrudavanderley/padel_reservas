from django.contrib import admin
from django.db.models import Count
from django.urls import path
from django.template.response import TemplateResponse
from datetime import date, timedelta
from .models import Pista, Reserva, Bloqueo

@admin.register(Pista)
class PistaAdmin(admin.ModelAdmin):
    list_display = ('id','nombre','activa')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id','usuario','pista','fecha','hora_inicio','hora_fin','estado')
    list_filter = ('estado','pista','fecha')
    search_fields = ('usuario__username','usuario__email')

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='dashboard'),
            path('ocupacion/', self.admin_site.admin_view(self.ocupacion_view), name='ocupacion'),
            path('calendario/', self.admin_site.admin_view(self.calendario_view), name='calendario-admin'),
        ]
        return custom + urls

    def dashboard_view(self, request):
        hoy = date.today()
        total_hoy = Reserva.objects.filter(fecha=hoy, estado='confirmada').count()
        total_mes = Reserva.objects.filter(fecha__gte=hoy.replace(day=1), estado='confirmada').count()
