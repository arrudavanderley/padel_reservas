import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padel_reservas.settings')
django.setup()

from django.contrib.auth.models import User

USERNAME = os.getenv("DJANGO_SUPERUSER_USERNAME")
EMAIL = os.getenv("DJANGO_SUPERUSER_EMAIL")
PASSWORD = os.getenv("DJANGO_SUPERUSER_PASSWORD")

if not USERNAME or not PASSWORD:
    print("Faltan variables de admin en Render")
    exit()

if User.objects.filter(username=USERNAME).exists():
    user = User.objects.get(username=USERNAME)
    user.set_password(PASSWORD)
    user.email = EMAIL
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"Superusuario {USERNAME} actualizado con nueva clave!")
else:
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print(f"Superusuario {USERNAME} creado!")
