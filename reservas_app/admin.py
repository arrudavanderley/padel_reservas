from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
import csv
from datetime import date, timedelta

from .models import Pista, Reserva, Bloqueo

# --- NO TOCAMOS USUARIOS PARA NO ROMPER ---

@admin.action(description="❌ Cancelar seleccionadas")
def cancelar_reservas(modeladmin, request, queryset):
    queryset.update(estado='cancelada')
    modeladmin.message_user(request, f"{queryset.count()} canceladas.")

@admin.action(description="📤 Exportar CSV")
def exportar_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=reservas.csv'
    writer = csv.writer(response)
    writer.writerow(['ID','Usuario','Email','Pista','Fecha','Inicio','Fin','Estado'])
    for r in queryset.select_related('usuario','pista'):
        writer.writerow([r.id, r.usuario.username, r.usuario.email, r.pista.nombre, r.fecha, r.hora_inicio, r.hora_fin, r.estado])
    return response

@admin.register(Pista)
class PistaAdmin(admin.ModelAdmin):
    list_display = ('id','nombre','activa')
    list_editable = ('activa',)

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id','usuario','pista','fecha','hora_inicio','hora_fin','estado','estado_badge')
    list_filter = ('estado','pista','fecha')
    search_fields = ('usuario__username','pista__nombre')
    date_hierarchy = 'fecha'
    actions = [cancelar_reservas, exportar_csv]
    list_per_page = 25

    def estado_badge(self, obj):
        color = '#16a34a' if obj.estado=='confirmada' else '#dc2626'
        bg = '#dcfce7' if obj.estado=='confirmada' else '#fee2e2'
        return format_html('<span style="background:{}; color:{}; padding:3px 8px; border-radius:999px; font-size:11px; font-weight:800;">{}</span>', bg, color, obj.estado)
    estado_badge.short_description = "Estado"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='reservas-dashboard'),
            path('ocupacion-hoy/', self.admin_site.admin_view(self.ocupacion_hoy_view), name='ocupacion-hoy'),
            path('calendario-admin/', self.admin_site.admin_view(self.calendario_admin_view), name='calendario-admin'),
        ]
        return custom + urls

    def dashboard_view(self, request):
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        hace_7 = hoy - timedelta(days=7)
        total_hoy = Reserva.objects.filter(fecha=hoy, estado='confirmada').count()
        total_mes = Reserva.objects.filter(fecha__gte=inicio_mes, estado='confirmada').count()
        por_pista = Reserva.objects.filter(fecha__gte=hoy-timedelta(days=30), estado='confirmada').values('pista__nombre').annotate(total=Count('id')).order_by('-total')
        por_dia_qs = Reserva.objects.filter(fecha__gte=hace_7).values('fecha').annotate(total=Count('id')).order_by('fecha')
        por_dia_labels=[x['fecha'].strftime('%d/%m') for x in por_dia_qs]
        por_dia_data=[x['total'] for x in por_dia_qs]
        bloqueos = Bloqueo.objects.filter(fecha_fin__gte=hoy).order_by('fecha_inicio')[:5]
        top_usuarios = Reserva.objects.filter(estado='confirmada').values('usuario__username').annotate(total=Count('id')).order_by('-total')[:5]

        context=dict(
            self.admin_site.each_context(request),
            total_hoy=total_hoy,
            total_mes=total_mes,
            ingresos_mes=total_mes*18,
            usuarios_activos=Reserva.objects.filter(fecha__gte=hace_7).values('usuario').distinct().count(),
            por_pista=por_pista,
            por_dia_labels=por_dia_labels,
            por_dia_data=por_dia_data,
            bloqueos=bloqueos,
            top_usuarios=top_usuarios,
            hoy=hoy,
            usuarios_limite=[],
        )
        return TemplateResponse(request, "admin/dashboard_padel.html", context)

    def ocupacion_hoy_view(self, request):
        hoy = date.today()
        reservas_hoy = Reserva.objects.filter(fecha=hoy, estado='confirmada').select_related('pista','usuario').order_by('hora_inicio')
        bloqueos_hoy = Bloqueo.objects.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy)
        pistas = Pista.objects.filter(activa=True)
        ocupacion=[]
        for pista in pistas:
            res_pista = reservas_hoy.filter(pista=pista)
            horas = len(res_pista)*1.5
            porc = int((horas/15)*100)
            ocupacion.append({'pista':pista,'count':res_pista.count(),'horas':horas,'porcentaje':min(porc,100),'reservas':res_pista})
        context=dict(
            self.admin_site.each_context(request),
            hoy=hoy,
            reservas_hoy=reservas_hoy,
            bloqueos_hoy=bloqueos_hoy,
            ocupacion=ocupacion,
            total_hoy=reservas_hoy.count(),
            total_slots=len(pistas)*10,
        )
        return TemplateResponse(request, "admin/ocupacion_hoy.html", context)

    def calendario_admin_view(self, request):
        pistas = Pista.objects.all()
        context=dict(self.admin_site.each_context(request), pistas=pistas)
        return TemplateResponse(request, "admin/calendario_admin.html", context)

@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ('pista','fecha_inicio','fecha_fin','motivo')
    
