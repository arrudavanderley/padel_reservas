# 🎾 Reservas de pádel

Proyecto web de reservas de pistas de pádel hecho con **Django** y **SQLite**, sin
pasarela de pago.

Puedes ver el calendario sin entrar, y reservar si te registras. Evita que dos personas reserven la misma pista a la misma hora y deja crear reservas recurrentes.

**🚀 Demo en vivo:** https://padel-reservas-zbpn.onrender.com

## Funcionalidades

- Calendario interactivo con FullCalendar para ver la disponibilidad.
- Validación para evitar solapamientos en la misma pista.
- Reservas recurrentes (diaria, semanal, mensual).
- Límite de 5 reservas activas por usuario.
- Bloqueos de pistas para mantenimiento desde el admin.
- Panel de administrador de Django.
- Registro y login de usuarios.

## Stack

Django, Python, SQLite, FullCalendar, WhiteNoise y Render para el deploy.

## Cómo ejecutarlo en local

```bash
# 1. Clonar el repo
git clone https://github.com/arrudavanderley/padel_reservas.git
cd padel_reservas

# 2. Crear entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear base de datos
python manage.py migrate

# 5. Crear tu admin
python manage.py createsuperuser

# 6. Arrancar
python manage.py runserver
```

Luego abre http://127.0.0.1:8000/ 
Entra en /admin con el superusuario que acabas de crear y crea las pistas (Pista 1, Pista 2, Pista 3).

## Notas

- Dejé el calendario público para consultar sin cuenta. Solo pide login al reservar.
- Al cancelar una reserva no la borro, la marco como cancelada para guardar el historial.
- Zona horaria: Europe/Madrid.
