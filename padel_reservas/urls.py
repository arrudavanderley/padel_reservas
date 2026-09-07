"""URLs raíz: el admin, y todo lo demás delegado a reservas_app.urls."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('reservas_app.urls')),
]
