from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.calendario, name='calendario'),
    path('eventos/', views.eventos_json, name='eventos_json'),

    path('reservas/crear/', views.crear_reserva, name='crear_reserva'),
    path('reservas/<int:reserva_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),

    path('bloqueos/', views.bloqueos_lista, name='bloqueos_lista'),
    path('bloqueos/<int:bloqueo_id>/eliminar/', views.bloqueo_eliminar, name='bloqueo_eliminar'),

    path('registro/', views.registro, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='reservas/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='calendario'), name='logout'),
]
