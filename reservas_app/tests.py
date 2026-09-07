"""
Tests: python manage.py test

Cubren la validación de solapamiento, las reservas recurrentes, el límite
de reservas activas por usuario, los permisos de cancelación y el envío de
emails.
"""
from datetime import date, timedelta, time

from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from .models import Bloqueo, Pista, Reserva, hay_solape
from .views import LIMITE_RESERVAS_ACTIVAS_POR_USUARIO


class SolapamientoTests(TestCase):
    def setUp(self):
        self.pista = Pista.objects.create(nombre='Pista de pruebas')
        self.usuario = User.objects.create_user('jugador1', password='clave-test-123')
        self.fecha = date.today() + timedelta(days=7)

    def test_pista_vacia_no_tiene_solape(self):
        solapa, _ = hay_solape(self.pista, self.fecha, time(10, 0), time(11, 0))
        self.assertFalse(solapa)

    def test_detecta_solape_con_otra_reserva(self):
        Reserva.objects.create(
            pista=self.pista, usuario=self.usuario, fecha=self.fecha,
            hora_inicio=time(10, 0), hora_fin=time(11, 0),
        )
        solapa, _ = hay_solape(self.pista, self.fecha, time(10, 30), time(11, 30))
        self.assertTrue(solapa)

    def test_franjas_contiguas_no_solapan(self):
        Reserva.objects.create(
            pista=self.pista, usuario=self.usuario, fecha=self.fecha,
            hora_inicio=time(10, 0), hora_fin=time(11, 0),
        )
        solapa, _ = hay_solape(self.pista, self.fecha, time(11, 0), time(12, 0))
        self.assertFalse(solapa)

    def test_detecta_solape_con_bloqueo(self):
        Bloqueo.objects.create(
            pista=self.pista, fecha_inicio=self.fecha, fecha_fin=self.fecha,
            hora_inicio=time(9, 0), hora_fin=time(12, 0), motivo='Mantenimiento',
        )
        solapa, _ = hay_solape(self.pista, self.fecha, time(10, 0), time(11, 0))
        self.assertTrue(solapa)

    def test_reserva_cancelada_no_bloquea_el_hueco(self):
        Reserva.objects.create(
            pista=self.pista, usuario=self.usuario, fecha=self.fecha,
            hora_inicio=time(10, 0), hora_fin=time(11, 0), estado='cancelada',
        )
        solapa, _ = hay_solape(self.pista, self.fecha, time(10, 0), time(11, 0))
        self.assertFalse(solapa)


class VistasReservaTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.pista = Pista.objects.create(nombre='Pista de pruebas')
        self.usuario = User.objects.create_user(
            'jugador1', password='clave-test-123', email='jugador1@example.com',
        )
        self.otro_usuario = User.objects.create_user('jugador2', password='clave-test-123')
        self.fecha = (date.today() + timedelta(days=7)).isoformat()

    def test_crear_reserva_requiere_login(self):
        respuesta = self.client.post(reverse('crear_reserva'), {})
        self.assertEqual(respuesta.status_code, 302)

    def test_crear_reserva_simple(self):
        self.client.login(username='jugador1', password='clave-test-123')
        respuesta = self.client.post(reverse('crear_reserva'), {
            'pista': self.pista.id, 'fecha': self.fecha,
            'hora_inicio': '10:00', 'hora_fin': '11:00',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()['success'])
        self.assertEqual(Reserva.objects.count(), 1)

    def test_crear_reserva_envia_email_de_confirmacion(self):
        self.client.login(username='jugador1', password='clave-test-123')
        self.client.post(reverse('crear_reserva'), {
            'pista': self.pista.id, 'fecha': self.fecha,
            'hora_inicio': '10:00', 'hora_fin': '11:00',
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('jugador1@example.com', mail.outbox[0].to)

    def test_no_permite_reserva_solapada(self):
        self.client.login(username='jugador1', password='clave-test-123')
        self.client.post(reverse('crear_reserva'), {
            'pista': self.pista.id, 'fecha': self.fecha,
            'hora_inicio': '10:00', 'hora_fin': '11:00',
        })
        respuesta = self.client.post(reverse('crear_reserva'), {
            'pista': self.pista.id, 'fecha': self.fecha,
            'hora_inicio': '10:30', 'hora_fin': '11:30',
        })
        self.assertFalse(respuesta.json()['success'])
        self.assertEqual(Reserva.objects.count(), 1)

    def test_reserva_recurrente_semanal_crea_varias_filas(self):
        self.client.login(username='jugador1', password='clave-test-123')
        fecha_fin = (date.today() + timedelta(days=28)).isoformat()
        respuesta = self.client.post(reverse('crear_reserva'), {
            'pista': self.pista.id, 'fecha': self.fecha,
            'hora_inicio': '10:00', 'hora_fin': '11:00',
            'recurrente': 'on', 'frecuencia': 'semanal',
            'fecha_fin_recurrencia': fecha_fin,
        })
        datos = respuesta.json()
        self.assertTrue(datos['success'])
        self.assertEqual(datos['creadas'], 4)
        self.assertEqual(Reserva.objects.count(), 4)

    def test_limite_de_reservas_activas_por_usuario(self):
        self.client.login(username='jugador1', password='clave-test-123')
        for i in range(LIMITE_RESERVAS_ACTIVAS_POR_USUARIO):
            fecha = (date.today() + timedelta(days=10 + i)).isoformat()
            respuesta = self.client.post(reverse('crear_reserva'), {
                'pista': self.pista.id, 'fecha': fecha,
                'hora_inicio': '10:00', 'hora_fin': '11:00',
            })
            self.assertTrue(respuesta.json()['success'])

        fecha_extra = (date.today() + timedelta(days=50)).isoformat()
        respuesta = self.client.post(reverse('crear_reserva'), {
            'pista': self.pista.id, 'fecha': fecha_extra,
            'hora_inicio': '10:00', 'hora_fin': '11:00',
        })
        self.assertFalse(respuesta.json()['success'])
        self.assertEqual(Reserva.objects.count(), LIMITE_RESERVAS_ACTIVAS_POR_USUARIO)

    def test_no_se_puede_cancelar_una_reserva_ajena(self):
        self.client.login(username='jugador1', password='clave-test-123')
        self.client.post(reverse('crear_reserva'), {
            'pista': self.pista.id, 'fecha': self.fecha,
            'hora_inicio': '10:00', 'hora_fin': '11:00',
        })
        reserva = Reserva.objects.first()

        self.client.logout()
        self.client.login(username='jugador2', password='clave-test-123')
        respuesta = self.client.post(reverse('cancelar_reserva', args=[reserva.id]))

        self.assertEqual(respuesta.status_code, 403)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'confirmada')

    def test_cancelar_reserva_envia_email(self):
        self.client.login(username='jugador1', password='clave-test-123')
        self.client.post(reverse('crear_reserva'), {
            'pista': self.pista.id, 'fecha': self.fecha,
            'hora_inicio': '10:00', 'hora_fin': '11:00',
        })
        reserva = Reserva.objects.first()
        mail.outbox.clear()

        self.client.post(reverse('cancelar_reserva', args=[reserva.id]))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('jugador1@example.com', mail.outbox[0].to)

    def test_calendario_es_visible_sin_iniciar_sesion(self):
        respuesta = self.client.get(reverse('calendario'))
        self.assertEqual(respuesta.status_code, 200)
