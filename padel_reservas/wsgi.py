"""
WSGI config for padel_reservas project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padel_reservas.settings')

application = get_wsgi_application()
