import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padel_reservas.settings')
django.setup()

from django.contrib.auth.models import User

USERNAME = os.getenv("DJANGO_SUPERUSER_USERNAME")
EMAIL = os.getenv("DJANGO_SUPERUSER_EMAIL")
PASSWORD = os.getenv("DJANGO_SUPERUSER_PASSWORD")

if not USERNAME or not PASSWORD:
    print("Faltan variables de admin en Render, no se crea nada")
    exit()

if not User.objects.filter(username=USERNAME).exists():
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print(f"Superusuario {USERNAME} creado!")
