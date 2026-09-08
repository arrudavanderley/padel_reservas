import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padel_reservas.settings')
django.setup()
from django.contrib.auth.models import User

USERNAME = "Arruda"
EMAIL = "arrudapedagogosocial@gmail.com"
PASSWORD = "padel1234@"

try:
    if User.objects.filter(username=USERNAME).exists():
        u = User.objects.get(username=USERNAME)
        u.set_password(PASSWORD)
        u.email = EMAIL
        u.is_staff = True
        u.is_superuser = True
        u.save()
        print(f"Superusuario {USERNAME} actualizado FORZADO!")
    else:
        User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
        print(f"Superusuario {USERNAME} creado FORZADO!")
except Exception as e:
    print(f"Error: {e}")
