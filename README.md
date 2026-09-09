# 🎾 Sistema de Reservas - Padel

Proyecto web de reservas de pistas de pádel con **diseño premium moderno**, hecho con Django, PostgreSQL y desplegado en Render. 100% funcional y responsive.

### ✨ Qué hace

Reserva tu pista en 20 segundos. Sistema pensado para clubes reales. Todo ficticio para demo, pero 100% funcional.

- Landing page moderna con hero, pistas, cómo funciona y contacto con mapa
- Calendario interactivo en tiempo real (FullCalendar)
- Reservas instantáneas con modal, sin recargar la página
- Confirmación automática por **email**

### 🚀 Funcionalidades

- **Calendario interactivo** con FullCalendar (vistas Mes/Semana/Día) y filtros por pista
- **Validación anti-solapamiento:** evita que 2 personas reserven la misma pista a la misma hora (con `select_for_update` para concurrencia)
- **Reservas recurrentes:** diaria, semanal y mensual con límite de seguridad (104 ocurrencias)
- **Límite de 5 reservas activas** por usuario (una recurrente cuenta como varias)
- **Bloqueos de pistas** por mantenimiento/eventos desde /bloqueos/ (solo staff)
- **Autenticación completa:** registro, login, logout con diseño premium
- **Confirmación por email:** al crear y cancelar reserva (configurable)
- **Diseño responsive premium:** Tailwind CSS, glass navbar, cards, animaciones
- **Botón de compartir nativo:** Web Share API + fallback con WhatsApp, X, Facebook, copiar link
- **Panel admin Django** completo
- **Persistencia real:** PostgreSQL en Render (no se borran las reservas)

### 🛠 Stack

- **Backend:** Django 5, Python 3.11
- **Base de datos:** PostgreSQL (Render) / SQLite en local
- **Frontend:** Tailwind CSS, FullCalendar 5, Font Awesome, Inter font
- **Deploy:** Render + WhiteNoise + Gunicorn
- **Email:** Django Email Backend (Gmail / Brevo / SendGrid)

### 💻 Cómo ejecutarlo en local

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

# 4. Variables de entorno (crea un .env o usa settings local)
# Para probar email en consola:
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# 5. Base de datos
python manage.py migrate

# 6. Admin
python manage.py createsuperuser

# 7. Arrancar
python manage.py runserver
```

Abre http://127.0.0.1:8000/ 
Entra en /admin con tu superuser y crea las pistas: Pista Central, Sunset, Pro (con colores #2563eb, #f97316, #0f172a).

### 📧 Configurar email real (gratis)

En `padel_reservas/settings.py` añade:

```python
# Email - para que lleguen confirmaciones de verdad
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # o smtp-relay.brevo.com si usas Brevo
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER') # tu email
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD') # app password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

En Render > Environment > añade:
- `EMAIL_HOST_USER` = tu gmail
- `EMAIL_HOST_PASSWORD` = app password de Gmail (16 caracteres)

Si no lo configuras, el código no falla por `fail_silently=True`, simplemente no llega el email.

### 📦 Estructura

```
padel_reservas/
├── padel_reservas/ (settings, urls principales)
├── reservas_app/
│   ├── models.py (Pista, Reserva, Bloqueo)
│   ├── views.py (home, calendario, eventos_json, crear/cancelar)
│   ├── forms.py (ReservaForm, RegistroForm, BloqueoForm)
│   └── templates/reservas/
│       ├── base.html (navbar glass + footer + compartir)
│       ├── home.html (landing premium)
│       ├── calendario.html (FullCalendar moderno)
│       ├── login.html / registro.html
│       └── bloqueos_lista.html
└── requirements.txt
```

### 📝 Notas

- Al cancelar, la reserva se marca como `cancelada`, no se borra, para guardar historial
- Zona horaria: Europe/Madrid
- Horario club (ficticio): 8:00-23:00, última reserva 21:30
- Contacto ficticio.
- Proyecto demo creado por Arruda Van der Ley - 2026

### 📄 Licencia

MIT - Úsalo libremente para tu portfolio.
