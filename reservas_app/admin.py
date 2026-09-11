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
        por_pista = Reserva.objects.filter(fecha__gte=hoy-timedelta(days=30), estado='confirmada').values('pista__nombre').annotate(total=Count('id')).order_by('-total')
        top = Reserva.objects.filter(estado='confirmada').values('usuario__username').annotate(total=Count('id')).order_by('-total')[:5]
        context = dict(self.admin_site.each_context(request), hoy=hoy, total_hoy=total_hoy, total_mes=total_mes, por_pista=por_pista, top_usuarios=top)
        return TemplateResponse(request, "admin/dashboard.html", context)

    def ocupacion_view(self, request):
        hoy = date.today()
        reservas = Reserva.objects.filter(fecha=hoy, estado='confirmada').select_related('pista','usuario').order_by('hora_inicio')
        context = dict(self.admin_site.each_context(request), hoy=hoy, reservas=reservas, total=reservas.count())
        return TemplateResponse(request, "admin/ocupacion.html", context)

    def calendario_view(self, request):
        pistas = Pista.objects.all()
        context = dict(self.admin_site.each_context(request), pistas=pistas)
        return TemplateResponse(request, "admin/calendario.html", context)

@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ('id','pista','fecha_inicio','fecha_fin','motivo')
