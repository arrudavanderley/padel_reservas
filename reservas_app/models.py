from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Pista(models.Model):
    """Una pista de pádel reservable."""

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    color = models.CharField(
        max_length=7,
        default='#1B4F72',
        help_text='Color hexadecimal para identificar esta pista en el calendario, por ejemplo #1B4F72.',
    )
    activa = models.BooleanField(
        default=True,
        help_text='Las pistas desactivadas no son reservables, pero conservan su historial.',
    )

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Pista'
        verbose_name_plural = 'Pistas'

    def __str__(self):
        return self.nombre


class Perfil(models.Model):
    """Datos adicionales de un usuario, aparte de los que ya trae Django."""

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f'Perfil de {self.usuario.username}'


@receiver(post_save, sender=User)
def crear_perfil_automaticamente(sender, instance, created, **kwargs):
    """Crea el Perfil de cada User nuevo, para poder asumir siempre que usuario.perfil existe."""
    if created:
        Perfil.objects.create(usuario=instance)


ESTADO_CONFIRMADA = 'confirmada'
ESTADO_CANCELADA = 'cancelada'
ESTADO_BLOQUEADA = 'bloqueada'

ESTADO_CHOICES = [
    (ESTADO_CONFIRMADA, 'Confirmada'),
    (ESTADO_CANCELADA, 'Cancelada'),
    (ESTADO_BLOQUEADA, 'Bloqueada'),
]

FRECUENCIA_CHOICES = [
    ('diaria', 'Diaria'),
    ('semanal', 'Semanal'),
    ('mensual', 'Mensual'),
]


class Reserva(models.Model):
    """Una franja horaria reservada por un usuario en una pista concreta."""

    pista = models.ForeignKey(Pista, on_delete=models.CASCADE, related_name='reservas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    recurrente = models.BooleanField(default=False)
    frecuencia = models.CharField(max_length=10, choices=FRECUENCIA_CHOICES, blank=True, null=True)
    fecha_fin_recurrencia = models.DateField(blank=True, null=True)

    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default=ESTADO_CONFIRMADA)

    # Filas generadas por una misma solicitud recurrente comparten este identificador.
    grupo_recurrencia = models.CharField(max_length=40, blank=True, null=True, editable=False)

    creada_el = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f'{self.pista} · {self.fecha} {self.hora_inicio}-{self.hora_fin} ({self.usuario})'

    def clean(self):
        """Validación a nivel de modelo: se aplica también al guardar desde el admin."""
        if self.hora_inicio and self.hora_fin and self.hora_fin <= self.hora_inicio:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')

        if self.estado == ESTADO_CONFIRMADA and self.pista_id and self.fecha:
            solapa, motivo = hay_solape(
                self.pista, self.fecha, self.hora_inicio, self.hora_fin,
                excluir_reserva_id=self.pk,
            )
            if solapa:
                raise ValidationError(motivo)


class Bloqueo(models.Model):
    """
    Franja (o varios días completos) en la que una pista no está disponible,
    por mantenimiento, un evento, etc. Para bloquear el día entero, usa
    hora_inicio=00:00 y hora_fin=23:59.
    """

    pista = models.ForeignKey(Pista, on_delete=models.CASCADE, related_name='bloqueos')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    motivo = models.TextField()

    class Meta:
        ordering = ['fecha_inicio', 'hora_inicio']
        verbose_name = 'Bloqueo'
        verbose_name_plural = 'Bloqueos'

    def __str__(self):
        return f'{self.pista} bloqueada {self.fecha_inicio} → {self.fecha_fin}'

    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')
        if self.hora_inicio and self.hora_fin and self.hora_fin <= self.hora_inicio:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')


def hay_solape(pista, fecha, hora_inicio, hora_fin, excluir_reserva_id=None):
    """
    Comprueba si [hora_inicio, hora_fin) de una fecha concreta choca con otra
    reserva confirmada o con un bloqueo, para la pista dada. Devuelve
    (hay_solape: bool, mensaje: str | None). Dos franjas contiguas (una
    termina cuando la otra empieza) no cuentan como solapadas.
    """
    reservas_que_chocan = Reserva.objects.filter(
        pista=pista, fecha=fecha, estado=ESTADO_CONFIRMADA,
        hora_inicio__lt=hora_fin, hora_fin__gt=hora_inicio,
    )
    if excluir_reserva_id:
        reservas_que_chocan = reservas_que_chocan.exclude(pk=excluir_reserva_id)

    if reservas_que_chocan.exists():
        return True, 'La pista ya está ocupada en ese horario.'

    bloqueos_que_chocan = Bloqueo.objects.filter(
        pista=pista, fecha_inicio__lte=fecha, fecha_fin__gte=fecha,
        hora_inicio__lt=hora_fin, hora_fin__gt=hora_inicio,
    )
    if bloqueos_que_chocan.exists():
        return True, 'Esa franja horaria está bloqueada (mantenimiento o evento).'

    return False, None
