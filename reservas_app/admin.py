from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.http import HttpResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils import timezone
import csv
from datetime import date, timedelta

from .models import Pista, Reserva, Bloqueo

# --- ADMIN DE USUARIOS MEJORADO: crear usuarios y asignar reservas ---
class ReservaInline(admin.TabularInline):
    model = Reserva
    extra = 0
    fields = ('pista', 'fecha', 'hora_inicio', 'hora_fin', 'estado')
    autocomplete_fields = ('pista',)
    readonly_fields = ('fecha',)

class UsuarioConReservasAdmin(BaseUserAdmin):
    inlines = [ReservaInline]
    list_display = ('username', 'email', 'first_name', 'is_staff', 'reservas_activas', 'total_reservas')
    actions = ['exportar_usuarios_csv']

    def reservas_activas(self, obj):
        activas = obj.reserva_set.filter(estado='confirmada', fecha__gte=date.today()).count()
        color = '#16a34a' if activas < 5 else '#dc2626'
        return format_html('<span style="background:{}; color:white; padding:3px 10px; border-radius:999px; font-weight:800; font-size:11px;">{}/5</span>', color, activas)
    reservas_activas.short_description = "Activas (límite 5)"

    def total_reservas(self, obj):
        return obj.reserva_set.count()
    total_reservas.short_description = "Total histórico"

    @admin.action(description="📤 Exportar usuarios con nº reservas")
    def exportar_usuarios_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=usuarios_padel.csv'
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Nombre', 'Activas', 'Total'])
        for u in queryset:
            activas = u.reserva_set.filter(estado='confirmada', fecha__gte=date.today()).count()
            total = u.reserva_set.count()
            writer.writerow([u.username, u.email, u.first_name, activas, total])
        return response

# Re-registrar User con nuestro admin mejorado
try:
    admin.site.unregister(User)
except:
    pass
admin.site.register(User, UsuarioConReservasAdmin)

# --- ACCIONES ---
@admin.action(description="❌ Cancelar seleccionadas")
def cancelar_reservas(modeladmin, request, queryset):
    queryset.update(estado='cancelada')
    modeladmin.message_user(request, f"{queryset.count()} canceladas.")

@admin.action(description="📤 Exportar a CSV")
def exportar_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=reservas.csv'
    writer = csv.writer(response)
    writer.writerow(['ID','Usuario','Email','Pista','Fecha','Inicio','Fin','Estado','Recurrente'])
    for r in queryset.select_related('usuario','pista'):
        writer.writerow([r.id, r.usuario.username, r.usuario.email, r.pista.nombre, r.fecha, r.hora_inicio, r.hora_fin, r.estado, r.recurrente])
    return response

@admin.register(Pista)
class PistaAdmin(admin.ModelAdmin):
    list_display = ('nombre','tipo','color_badge','precio_hora','activa','total_reservas_hoy')
    list_editable = ('activa','precio_hora')
    search_fields = ('nombre',)

    def color_badge(self, obj):
        return format_html('<span style="background:{}; color:white; padding:4px 10px; border-radius:999px; font-size:11px; font-weight:700;">{}</span>', getattr(obj,'color','#2563eb'), getattr(obj,'color','#2563eb'))
    color_badge.short_description = "Color"

    def total_reservas_hoy(self, obj):
        hoy = date.today()
        return obj.reserva_set.filter(fecha=hoy, estado='confirmada').count()
    total_reservas_hoy.short_description = "Hoy"

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id','usuario_link','pista_color','fecha','horario','estado_badge','recurrente_icon','creada_en')
    list_filter = ('estado','pista','recurrente','fecha')
    search_fields = ('usuario__username','usuario__email','pista__nombre')
    date_hierarchy = 'fecha'
    list_per_page = 25
    actions = [cancelar_reservas, exportar_csv]
    autocomplete_fields = ('usuario','pista')
    readonly_fields = ('creada_en',)

    def usuario_link(self, obj):
        activas = obj.usuario.reserva_set.filter(estado='confirmada', fecha__gte=date.today()).count()
        return format_html('<b>{}</b> <span style="background:{}; color:white; padding:2px 6px; border-radius:999px; font-size:10px;">{}/5</span><br><span style="font-size:11px; color:#64748b;">{}</span>', obj.usuario.username, '#dc2626' if activas>=5 else '#16a34a', activas, obj.usuario.email)
    usuario_link.short_description = "Usuario (límite 5)"

    def pista_color(self, obj):
        return format_html('<span style="display:inline-block; width:10px; height:10px; background:{}; border-radius:50%; margin-right:6px;"></span>{}', getattr(obj.pista,'color','#2563eb'), obj.pista.nombre)
    pista_color.short_description = "Pista"

    def horario(self, obj):
        return f"{obj.hora_inicio.strftime('%H:%M')} - {obj.hora_fin.strftime('%H:%M')}"
    
    def estado_badge(self, obj):
        colores = {'confirmada':'#dcfce7,#16a34a','cancelada':'#fee2e2,#dc2626','usada':'#dbeafe,#2563eb'}
        bg,fg = colores.get(obj.estado,'#f1f5f9,#475569').split(',')
        return format_html('<span style="background:{}; color:{}; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:800; text-transform:uppercase;">{}</span>', bg,fg,obj.estado)
    estado_badge.short_description="Estado"

    def recurrente_icon(self, obj):
        return "🔁 Sí" if obj.recurrente else "—"

    # Validación límite 5 en admin también
    def save_model(self, request, obj, form, change):
        if not change: # solo al crear
            activas = Reserva.objects.filter(usuario=obj.usuario, estado='confirmada', fecha__gte=date.today()).count()
            if activas >=5:
                from django.contrib import messages
                messages.error(request, f"❌ {obj.usuario.username} ya tiene {activas}/5 reservas activas. Cancela alguna primero.")
                return
        super().save_model(request,obj,form,change)

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
        usuarios_activos = Reserva.objects.filter(fecha__gte=hace_7).values('usuario').distinct().count()
        ingresos_mes = 0
        for r in Reserva.objects.filter(fecha__gte=inicio_mes, estado='confirmada').select_related('pista'):
            try:
                from datetime import datetime
                precio=float(getattr(r.pista,'precio_hora',18))
                inicio=datetime.combine(date.today(), r.hora_inicio)
                fin=datetime.combine(date.today(), r.hora_fin)
                horas=(fin-inicio).seconds/3600
                ingresos_mes+=horas*precio
            except:
                pass
        por_pista = Reserva.objects.filter(fecha__gte=hoy-timedelta(days=30), estado='confirmada').values('pista__nombre').annotate(total=Count('id')).order_by('-total')
        por_dia_qs = Reserva.objects.filter(fecha__gte=hace_7).values('fecha').annotate(total=Count('id')).order_by('fecha')
        por_dia_labels=[x['fecha'].strftime('%d/%m') for x in por_dia_qs]
        por_dia_data=[x['total'] for x in por_dia_qs]
        proximos_bloqueos = Bloqueo.objects.filter(fecha_fin__gte=hoy).order_by('fecha_inicio')[:5]
        top_usuarios = Reserva.objects.filter(estado='confirmada').values('usuario__username').annotate(total=Count('id')).order_by('-total')[:5]
        usuarios_limite = User.objects.all()
        lista_limite=[]
        for u in usuarios_limite:
            activas=u.reserva_set.filter(estado='confirmada', fecha__gte=hoy).count()
            if activas>=4:
                lista_limite.append({'username':u.username,'email':u.email,'activas':activas})

        context=dict(
            self.admin_site.each_context(request),
            total_hoy=total_hoy,
            total_mes=total_mes,
            ingresos_mes=int(ingresos_mes),
            usuarios_activos=usuarios_activos,
            por_pista=por_pista,
            por_dia_labels=por_dia_labels,
            por_dia_data=por_dia_data,
            bloqueos=proximos_bloqueos,
            top_usuarios=top_usuarios,
            usuarios_limite=lista_limite,
            hoy=hoy,
        )
        return TemplateResponse(request, "admin/dashboard_padel.html", context)

    def ocupacion_hoy_view(self, request):
        hoy = date.today()
        reservas_hoy = Reserva.objects.filter(fecha=hoy, estado='confirmada').select_related('pista','usuario').order_by('hora_inicio')
        bloqueos_hoy = Bloqueo.objects.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy)
        # ocupación por pista
        pistas = Pista.objects.filter(activa=True)
        ocupacion=[]
        for pista in pistas:
            res_pista = reservas_hoy.filter(pista=pista)
            horas_ocupadas = len(res_pista) * 1.5 # 90min =1.5h
            porcentaje = int((horas_ocupadas / 15) * 100) # 15h abiertas
            ocupacion.append({'pista':pista,'count':res_pista.count(),'horas':horas_ocupadas,'porcentaje':min(porcentaje,100),'reservas':res_pista})

        context=dict(
            self.admin_site.each_context(request),
            hoy=hoy,
            reservas_hoy=reservas_hoy,
            bloqueos_hoy=bloqueos_hoy,
            ocupacion=ocupacion,
            total_hoy=reservas_hoy.count(),
            total_slots= len(pistas)*10,
        )
        return TemplateResponse(request, "admin/ocupacion_hoy.html", context)

    def calendario_admin_view(self, request):
        pistas = Pista.objects.all()
        context=dict(
            self.admin_site.each_context(request),
            pistas=pistas,
        )
        return TemplateResponse(request, "admin/calendario_admin.html", context)

@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ('pista','fecha_inicio','fecha_fin','horario','motivo','activo_hoy')
    list_filter = ('pista','fecha_inicio')
    def horario(self,obj): return f"{obj.hora_inicio.strftime('%H:%M')} - {obj.hora_fin.strftime('%H:%M')}"
    def activo_hoy(self,obj):
        hoy=date.today()
        activo=obj.fecha_inicio <= hoy <= obj.fecha_fin
        if activo:
            return format_html('<span style="background:#fee2e2; color:#dc2626; padding:3px 8px; border-radius:999px; font-size:11px; font-weight:800;">ACTIVO HOY</span>')
        return "—"
    
