"""
Configuración del proyecto: Sistema de reservas de pistas de pádel.

Las variables sensibles (SECRET_KEY, DEBUG, ALLOWED_HOSTS, email...) se leen
de un archivo .env en la raíz del proyecto — ver .env.example.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


# --- Seguridad -------------------------------------------------------------

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-clave-de-desarrollo-cambia-esto-antes-de-desplegar',
)
DEBUG = os.getenv('DEBUG', 'True').strip().lower() == 'true'
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    if host.strip()
]


# --- Aplicaciones ------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reservas_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'padel_reservas.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'padel_reservas.wsgi.application'


# --- Base de datos -----------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- Validación de contraseñas ------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internacionalización -----------------------------------------------------

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'  # Cambia esto si el club está en otro país
USE_I18N = True
USE_TZ = True


# --- Archivos estáticos --------------------------------------------------------

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Autenticación ---------------------------------------------------------------

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'calendario'
LOGOUT_REDIRECT_URL = 'calendario'


# --- Email -------------------------------------------------------------------
# Por defecto, los emails se imprimen en la terminal donde corre runserver
# (útil en desarrollo, no requiere ninguna cuenta de correo real). Para enviar
# emails de verdad, define estas variables en tu .env con los datos de tu
# proveedor SMTP y cambia EMAIL_BACKEND a 'django.core.mail.backends.smtp.EmailBackend'.

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').strip().lower() == 'true'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'reservas@localhost')
