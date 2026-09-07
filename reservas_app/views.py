"""
Vistas del sistema de reservas.

- calendario: página principal, pública.
- eventos_json: API que alimenta a FullCalendar (reservas + bloqueos).
- crear_reserva / cancelar_reserva: requieren login.
- registro / login / logout: gestión de cuentas.
- bloqueos_lista / bloqueo_eliminar: solo para staff.

El calendario es visible sin cuenta; reservar y cancelar requieren haber
iniciado sesión.
"""

import calendar as calendar_mod
import uuid
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import BloqueoForm, RegistroForm, ReservaForm
from .models import Bloqueo, ESTADO_CANCELADA, ESTADO_CONFIRMADA, Pista, Reserva, hay_solape

# Límite de seguridad para reservas recurrentes (evita generar miles de filas
# de golpe por un despiste en el formulario).
LIMITE_OCURRENCIAS_RECURRENCIA = 104  # ~2 años en semanal, ~3 meses en diaria

# Máximo de reservas confirmadas y futuras que puede tener un mismo usuario
# a la vez. Una reserva recurrente cuenta como varias.
LIMITE_RESERVAS_ACTIVAS_POR_USUARIO = 5


def sumar_periodo(fecha_actual, frecuencia):
    """Devuelve la siguiente fecha según la frecuencia elegida."""
    if frecuencia == 'diaria':
        return fecha_actual + timedelta(days=1)
    if frecuencia == 'semanal':
        return fecha_actual + timedelta(weeks=1)
    if frecuencia == 'mensual':
        mes = fecha_actual.month + 1
        anio = fecha_actual.year
        if mes > 12:
            mes = 1
            anio += 1
        ultimo_dia_del_mes = calendar_mod.monthrange(anio, mes)[1]
        dia = min(fecha_actual.day, ultimo_dia_del_mes)
        return date(anio, mes, dia)
    return fecha_actual


def _enviar_email_confirmacion(usuario, pista, fechas, hora_inicio, hora_fin):
    """Envía un email de confirmación. No lanza excepción si falla el envío."""
    if not usuario.email:
        return

    rango_horario = f'{hora_inicio.strftime("%H:%M")} - {hora_fin.strftime("%H:%M")}'
    saludo = f'Hola {usuario.first_name or usuario.username},'

    if len(fechas) == 1:
        cuerpo = (
            f'{saludo}\n\nTu reserva ha sido confirmada:\n'
            f'Pista: {pista.nombre}\n'
            f'Fecha: {fechas[0].strftime("%d/%m/%Y")}\n'
            f'Hora: {rango_horario}\n\n¡Nos vemos en la pista!'
        )
    else:
        listado = '\n'.join(f'- {f.strftime("%d/%m/%Y")}' for f in fechas[:10])
        if len(fechas) > 10:
            listado += f'\n... y {len(fechas) - 10} fecha(s) más'
        cuerpo = (
            f'{saludo}\n\nSe han confirmado {len(fechas)} reservas recurrentes:\n'
            f'Pista: {pista.nombre}\nHora: {rango_horario}\nFechas:\n{listado}\n\n'
            f'¡Nos vemos en la pista!'
        )

    send_mail(
        subject='Reserva confirmada · Pádel',
        message=cuerpo,
        from_email=None,  # usa DEFAULT_FROM_EMAIL
        recipient_list=[usuario.email],
        fail_silently=True,
    )


def _enviar_email_cancelacion(reserva):
    """Envía un email de aviso de cancelación. No lanza excepción si falla el envío."""
    if not reserva.usuario.email:
        return
    cuerpo = (
        f'Hola {reserva.usuario.first_name or reserva.usuario.username},\n\n'
        f'Se ha cancelado tu reserva:\n'
        f'Pista: {reserva.pista.nombre}\n'
        f'Fecha: {reserva.fecha.strftime("%d/%m/%Y")}\n'
        f'Hora: {reserva.hora_inicio.strftime("%H:%M")} - {reserva.hora_fin.strftime("%H:%M")}'
    )
    send_mail(
        subject='Reserva cancelada · Pádel',
        message=cuerpo,
        from_email=None,
        recipient_list=[reserva.usuario.email],
        fail_silently=True,
    )


def calendario(request):
    pistas = Pista.objects.filter(activa=True)
    return render(request, 'reservas/calendario.html', {'pistas': pistas})


@require_GET
def eventos_json(request):
    """Reservas confirmadas y bloqueos, en el formato que espera FullCalendar."""
    inicio_str = request.GET.get('start', '')[:10]
    fin_str = request.GET.get('end', '')[:10]
    pista_id = request.GET.get('pista')

    reservas = Reserva.objects.filter(estado=ESTADO_CONFIRMADA).select_related('pista', 'usuario')
    if inicio_str:
        reservas = reservas.filter(fecha__gte=inicio_str)
    if fin_str:
        reservas = reservas.filter(fecha__lte=fin_str)
    if pista_id:
        reservas = reservas.filter(pista_id=pista_id)

    eventos = []
    for reserva in reservas:
        es_propia = request.user.is_authenticated and reserva.usuario_id == request.user.id
        nombre_usuario = reserva.usuario.get_full_name() or reserva.usuario.username
        eventos.append({
            'id': f'reserva-{reserva.id}',
            'title': f'{reserva.pista.nombre} · {nombre_usuario}',
            'start': f'{reserva.fecha.isoformat()}T{reserva.hora_inicio.isoformat()}',
            'end': f'{reserva.fecha.isoformat()}T{reserva.hora_fin.isoformat()}',
            'color': reserva.pista.color,
            'extendedProps': {'tipo': 'reserva', 'propia': es_propia, 'pista_id': reserva.pista_id},
        })

    # Un bloqueo puede abarcar varios días: se genera un evento por cada día
    # del rango (acotado a lo que pide FullCalendar) para que se vea bien en
    # las vistas de semana y de día.
    bloqueos = Bloqueo.objects.select_related('pista')
    if pista_id:
        bloqueos = bloqueos.filter(pista_id=pista_id)

    limite_inicio = date.fromisoformat(inicio_str) if inicio_str else None
    limite_fin = date.fromisoformat(fin_str) if fin_str else None

    for bloqueo in bloqueos:
        dia = bloqueo.fecha_inicio
        fin_rango = bloqueo.fecha_fin
        if limite_inicio and limite_inicio > dia:
            dia = limite_inicio
        if limite_fin and limite_fin < fin_rango:
            fin_rango = limite_fin

        while dia <= fin_rango:
            eventos.append({
                'id': f'bloqueo-{bloqueo.id}-{dia.isoformat()}',
                'title': f'Bloqueado: {bloqueo.motivo}',
                'start': f'{dia.isoformat()}T{bloqueo.hora_inicio.isoformat()}',
                'end': f'{dia.isoformat()}T{bloqueo.hora_fin.isoformat()}',
                'color': '#6c757d',
                'display': 'block',
                'extendedProps': {'tipo': 'bloqueo', 'pista_id': bloqueo.pista_id},
            })
            dia += timedelta(days=1)

    return JsonResponse(eventos, safe=False)


@login_required
@require_POST
def crear_reserva(request):
    """
    Crea una reserva (o varias, si es recurrente). Antes de guardar nada:
    1. Comprueba el límite de reservas activas del usuario.
    2. Dentro de una transacción, bloquea la fila de la pista implicada
       (select_for_update) y comprueba el solapamiento de todas las fechas.

    Nota sobre select_for_update() y SQLite: PostgreSQL y MySQL sí aplican
    un bloqueo real de fila, así que dos peticiones simultáneas sobre la
    misma pista se procesan una detrás de otra. SQLite no soporta bloqueo de
    filas (Reserva.objects.select_for_update() no da error, pero tampoco
    bloquea nada), así que en SQLite esta llamada no aporta protección extra
    frente a condiciones de carrera; la comprobación de hay_solape() de más
    abajo sigue siendo la principal defensa. Si en el futuro migras a
    PostgreSQL, este mismo código empezará a ofrecer la protección completa
    sin cambiar nada.
    """
    form = ReservaForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errores': form.errors}, status=400)

    datos = form.cleaned_data
    fechas = [datos['fecha']]

    if datos['recurrente']:
        fecha_actual = datos['fecha']
        while True:
            fecha_actual = sumar_periodo(fecha_actual, datos['frecuencia'])
            if fecha_actual > datos['fecha_fin_recurrencia']:
                break
            fechas.append(fecha_actual)
            if len(fechas) >= LIMITE_OCURRENCIAS_RECURRENCIA:
                break

    reservas_activas = Reserva.objects.filter(
        usuario=request.user, estado=ESTADO_CONFIRMADA, fecha__gte=date.today(),
    ).count()
    if reservas_activas + len(fechas) > LIMITE_RESERVAS_ACTIVAS_POR_USUARIO:
        return JsonResponse({
            'success': False,
            'errores': {'__all__': [
                f'Solo puedes tener {LIMITE_RESERVAS_ACTIVAS_POR_USUARIO} reservas activas a la '
                f'vez (ahora mismo tienes {reservas_activas}). Cancela alguna reserva futura '
                f'antes de crear otra.'
            ]},
        }, status=409)

    with transaction.atomic():
        Pista.objects.select_for_update().get(pk=datos['pista'].pk)

        conflictos = []
        for fecha in fechas:
            solapa, motivo = hay_solape(datos['pista'], fecha, datos['hora_inicio'], datos['hora_fin'])
            if solapa:
                conflictos.append(f'{fecha.strftime("%d/%m/%Y")}: {motivo}')
        if conflictos:
            return JsonResponse({'success': False, 'errores': {'__all__': conflictos}}, status=409)

        grupo_id = str(uuid.uuid4()) if len(fechas) > 1 else None
        reservas_creadas = [
            Reserva.objects.create(
                pista=datos['pista'], usuario=request.user, fecha=fecha,
                hora_inicio=datos['hora_inicio'], hora_fin=datos['hora_fin'],
                recurrente=datos['recurrente'], frecuencia=datos.get('frecuencia') or None,
                fecha_fin_recurrencia=datos.get('fecha_fin_recurrencia'), grupo_recurrencia=grupo_id,
            )
            for fecha in fechas
        ]

    _enviar_email_confirmacion(request.user, datos['pista'], fechas, datos['hora_inicio'], datos['hora_fin'])

    return JsonResponse({'success': True, 'creadas': len(reservas_creadas)})


@login_required
@require_POST
def cancelar_reserva(request, reserva_id):
    """Cancela (no borra) una reserva propia, o cualquiera si eres staff."""
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    if reserva.usuario_id != request.user.id and not request.user.is_staff:
        return JsonResponse(
            {'success': False, 'error': 'No tienes permiso para cancelar esta reserva.'}, status=403,
        )
    reserva.estado = ESTADO_CANCELADA
    reserva.save(update_fields=['estado'])
    _enviar_email_cancelacion(reserva)
    return JsonResponse({'success': True})


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            telefono = form.cleaned_data.get('telefono')
            if telefono:
                usuario.perfil.telefono = telefono
                usuario.perfil.save(update_fields=['telefono'])
            login(request, usuario)
            messages.success(request, '¡Cuenta creada correctamente! Ya puedes reservar pista.')
            return redirect('calendario')
    else:
        form = RegistroForm()
    return render(request, 'reservas/registro.html', {'form': form})


@staff_member_required(login_url='login')
def bloqueos_lista(request):
    """Vista exclusiva de staff: listar y crear bloqueos (alternativa rápida al admin)."""
    if request.method == 'POST':
        form = BloqueoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bloqueo creado correctamente.')
            return redirect('bloqueos_lista')
    else:
        form = BloqueoForm()

    bloqueos = Bloqueo.objects.select_related('pista').order_by('-fecha_inicio')
    return render(request, 'reservas/bloqueos_lista.html', {'form': form, 'bloqueos': bloqueos})


@staff_member_required(login_url='login')
@require_POST
def bloqueo_eliminar(request, bloqueo_id):
    bloqueo = get_object_or_404(Bloqueo, pk=bloqueo_id)
    bloqueo.delete()
    messages.success(request, 'Bloqueo eliminado.')
    return redirect('bloqueos_lista')
