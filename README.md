# 🎾 Sistema de Reservas · Pádel

Aplicación web de reservas para un club de pádel, construida con Django. Calendario de disponibilidad en tiempo real, reservas sin solapamiento (incluso con varios usuarios a la vez), recurrencia semanal/diaria/mensual, y un panel de administración propio pensado para gestionar el día a día del club sin tocar código.

Datos y club ficticios — es un proyecto de demostración, pero la lógica de reservas es la que usaría un club real.

## Qué hace

- **Calendario por franjas**: en vez de un calendario genérico, cada día se muestra como una rejilla de franjas de 90 minutos por pista, coloreada según disponibilidad (libre / tuya / ocupada / bloqueada). Reservar es tocar un hueco libre y confirmar — sin escribir horas a mano.
- **Sin solapamientos, ni con tráfico simultáneo**: la validación comprueba huecos y bloqueos antes de guardar, dentro de una transacción con bloqueo de fila (`select_for_update`) sobre la pista implicada.
- **Reservas recurrentes** (diaria, semanal o mensual), con límite de seguridad para no generar cientos de filas por error.
- **Límite de reservas activas por usuario**, configurable.
- **Bloqueos administrativos** (mantenimiento, eventos) que el calendario respeta igual que una reserva real.
- **Email de confirmación y cancelación**, con backend de consola por defecto (no requiere cuenta de correo para probar el proyecto) y SMTP real opcional.
- **Panel de administración unificado**: dashboard, calendario (con nombres reales de usuario y cancelación desde ahí) y accesos a Reservas/Pistas/Bloqueos/Usuarios en una sola página con navegación por anclas, tema oscuro de extremo a extremo — incluidas las pantallas estándar de Django que no tienen plantilla propia.

## Stack

- **Backend**: Django 5, Python 3.11
- **Base de datos**: SQLite por defecto (vía `dj_database_url`; se cambia a Postgres u otra en producción con una sola variable de entorno, sin tocar código)
- **Frontend**: Tailwind CSS (CDN), Font Awesome, tipografía Inter — calendario y rejilla de disponibilidad son JavaScript propio, sin librerías de calendario de terceros
- **Email**: `django.core.mail`, backend de consola en desarrollo / SMTP (Gmail, Brevo, SendGrid...) en producción
- **Deploy**: Render + WhiteNoise + Gunicorn

## Cómo ejecutarlo en local

```bash
# 1. Clonar
git clone https://github.com/arrudavanderley/padel_reservas.git
cd padel_reservas

# 2. Entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
# Copia .env.example a .env (o usa las variables de tu entorno) y revisa
# al menos SECRET_KEY. Para probar el email sin cuenta real, deja:
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# 5. Base de datos
python manage.py migrate

# 6. Superusuario
python manage.py createsuperuser

# 7. Arrancar
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. Entra en `/admin/` con el superusuario y crea tus pistas (nombre, color hexadecimal para el calendario — por ejemplo `#2563eb`).

## Configurar email real (gratis)

En Render (o tu `.env` local), define:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com          # o smtp-relay.brevo.com si usas Brevo
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
DEFAULT_FROM_EMAIL=tu_email@gmail.com
```

Con Gmail, `EMAIL_HOST_PASSWORD` es una **contraseña de aplicación** de 16 caracteres, no la contraseña normal de la cuenta. Si no configuras nada, el proyecto sigue funcionando igual: `fail_silently=True` hace que un email fallido nunca bloquee una reserva, simplemente no llega el correo.

## Estructura

```
padel_reservas/
├── padel_reservas/              # settings, urls raíz, wsgi
├── reservas_app/
│   ├── models.py                # Pista, Perfil, Reserva, Bloqueo, hay_solape()
│   ├── views.py                 # home, calendario, eventos_json, crear/cancelar_reserva...
│   ├── forms.py                 # ReservaForm, RegistroForm, BloqueoForm
│   ├── admin.py                 # Panel de administración: sin acciones masivas,
│   │                             títulos propios, Dashboard/Calendario embebidos en /admin/
│   ├── fixtures/datos_prueba.json
│   ├── migrations/
│   ├── static/reservas/{css,js}/
│   └── templates/
│       ├── reservas/            # base.html, home.html, calendario.html, login.html,
│       │                          registro.html, bloqueos_lista.html
│       └── admin/               # base_site.html (tema oscuro + nav de todo /admin/),
│                                   index.html (panel unificado)
├── requirements.txt
└── manage.py
```

## Notas

- Cancelar una reserva la marca como `cancelada`; no se borra, para conservar el historial.
- Zona horaria: `Europe/Madrid`.
- Horario del club (ficticio): 8:00–23:00, última reserva a las 21:30, franjas de 90 minutos.
- El panel de administración no tiene acciones masivas ni casillas de selección a propósito: cada modelo ya tiene su propio botón de eliminar en la pantalla de edición.
- Contacto y datos del club, ficticios.
- Proyecto demo creado por Arruda Van der Ley — 2026.

## Licencia

MIT — úsalo libremente para tu portfolio.
