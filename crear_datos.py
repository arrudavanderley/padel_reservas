import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padel_reservas.settings')
django.setup()

from reservas_app.models import Pista

print("Creando pistas...")
Pista.objects.get_or_create(nombre="Pista 1", defaults={"color": "#22c55e"})
Pista.objects.get_or_create(nombre="Pista 2", defaults={"color": "#3b82f6"})
Pista.objects.get_or_create(nombre="Pista 3", defaults={"color": "#f59e0b"})
print("Pistas listas!")
