/**
 * Calendario de reservas: FullCalendar + llamadas a la API en /eventos/,
 * /reservas/crear/ y /reservas/<id>/cancelar/. Usa USUARIO_AUTENTICADO,
 * USUARIO_STAFF y URL_LOGIN, definidas en calendario.html.
 */
document.addEventListener('DOMContentLoaded', function () {
    const calendarioEl = document.getElementById('calendario');
    const filtroPista = document.getElementById('filtro-pista');
    const modalReserva = new bootstrap.Modal(document.getElementById('modalReserva'));
    const modalDetalle = new bootstrap.Modal(document.getElementById('modalDetalle'));
    const mensajeError = document.getElementById('mensaje-error');

    function obtenerCookie(nombre) {
        const valor = `; ${document.cookie}`;
        const partes = valor.split(`; ${nombre}=`);
        if (partes.length === 2) {
            return partes.pop().split(';').shift();
        }
        return null;
    }
    const csrftoken = obtenerCookie('csrftoken');

    const calendar = new FullCalendar.Calendar(calendarioEl, {
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay',
        },
        initialView: 'dayGridMonth',
        slotMinTime: '07:00:00',
        slotMaxTime: '23:00:00',
        allDaySlot: false,
        height: 'auto',
        nowIndicator: true,

        events: function (info, exitoCallback, fracasoCallback) {
            const parametros = new URLSearchParams({ start: info.startStr, end: info.endStr });
            if (filtroPista.value) {
                parametros.append('pista', filtroPista.value);
            }
            fetch('/eventos/?' + parametros.toString())
                .then((respuesta) => respuesta.json())
                .then(exitoCallback)
                .catch(fracasoCallback);
        },

        dateClick: function (info) {
            if (!USUARIO_AUTENTICADO) {
                window.location.href = URL_LOGIN + '?next=/';
                return;
            }
            abrirModalReserva(info.dateStr);
        },

        eventClick: function (info) {
            mostrarDetalle(info.event);
        },
    });
    calendar.render();

    filtroPista.addEventListener('change', () => calendar.refetchEvents());

    document.getElementById('id_recurrente').addEventListener('change', function () {
        document.getElementById('campos-recurrencia').classList.toggle('d-none', !this.checked);
    });

    function abrirModalReserva(fechaInicioStr) {
        mensajeError.classList.add('d-none');
        document.getElementById('form-reserva').reset();
        document.getElementById('campos-recurrencia').classList.add('d-none');

        // fechaInicioStr es "2026-09-10" en vista de mes, o
        // "2026-09-10T10:00:00" en vista de semana/día.
        const [fecha, horaCompleta] = fechaInicioStr.split('T');
        document.getElementById('id_fecha').value = fecha;
        if (horaCompleta) {
            document.getElementById('id_hora_inicio').value = horaCompleta.substring(0, 5);
        }
        modalReserva.show();
    }

    document.getElementById('btn-guardar-reserva').addEventListener('click', function () {
        const datos = new FormData(document.getElementById('form-reserva'));
        if (!document.getElementById('id_recurrente').checked) {
            datos.delete('frecuencia');
            datos.delete('fecha_fin_recurrencia');
        }

        fetch('/reservas/crear/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            body: datos,
        })
            .then((respuesta) => respuesta.json())
            .then((datosRespuesta) => {
                if (datosRespuesta.success) {
                    modalReserva.hide();
                    calendar.refetchEvents();
                } else {
                    const errores = datosRespuesta.errores || { general: [datosRespuesta.error || 'No se pudo crear la reserva.'] };
                    mensajeError.textContent = Object.values(errores).flat().join(' ');
                    mensajeError.classList.remove('d-none');
                }
            })
            .catch(() => {
                mensajeError.textContent = 'No se pudo conectar con el servidor. Inténtalo de nuevo.';
                mensajeError.classList.remove('d-none');
            });
    });

    let reservaActualId = null;

    function mostrarDetalle(evento) {
        const propiedades = evento.extendedProps;
        const inicio = evento.start.toLocaleString('es-ES', { dateStyle: 'medium', timeStyle: 'short' });
        const fin = evento.end
            ? evento.end.toLocaleTimeString('es-ES', { timeStyle: 'short' })
            : '';

        document.getElementById('detalle-contenido').innerHTML =
            `<p class="mb-1"><strong>${evento.title}</strong></p><p class="text-muted">${inicio} – ${fin}</p>`;

        const botonCancelar = document.getElementById('btn-cancelar-reserva');
        if (propiedades.tipo === 'reserva' && (propiedades.propia || USUARIO_STAFF)) {
            reservaActualId = evento.id.replace('reserva-', '');
            botonCancelar.classList.remove('d-none');
        } else {
            botonCancelar.classList.add('d-none');
            reservaActualId = null;
        }
        modalDetalle.show();
    }

    document.getElementById('btn-cancelar-reserva').addEventListener('click', function () {
        if (!reservaActualId || !confirm('¿Seguro que quieres cancelar esta reserva?')) {
            return;
        }
        fetch(`/reservas/${reservaActualId}/cancelar/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
        })
            .then((respuesta) => respuesta.json())
            .then((datos) => {
                if (datos.success) {
                    modalDetalle.hide();
                    calendar.refetchEvents();
                } else {
                    alert(datos.error || 'No se pudo cancelar la reserva.');
                }
            });
    });
});
