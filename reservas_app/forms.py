from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Bloqueo, FRECUENCIA_CHOICES, Pista


class RegistroForm(UserCreationForm):
    """Alta de usuarios: añade email y teléfono al UserCreationForm de Django."""

    email = forms.EmailField(required=True)
    telefono = forms.CharField(required=False, max_length=20, label='Teléfono (opcional)')

    class Meta:
        model = User
        fields = ['username', 'email', 'telefono', 'password1', 'password2']


class ReservaForm(forms.Form):
    """
    Datos de una reserva, incluida la recurrencia. Es un Form (no un
    ModelForm) porque una solicitud recurrente puede generar varias filas
    de Reserva; la vista crear_reserva se encarga de eso.
    """

    pista = forms.ModelChoiceField(queryset=Pista.objects.filter(activa=True))
    fecha = forms.DateField()
    hora_inicio = forms.TimeField()
    hora_fin = forms.TimeField()

    recurrente = forms.BooleanField(required=False)
    frecuencia = forms.ChoiceField(choices=FRECUENCIA_CHOICES, required=False)
    fecha_fin_recurrencia = forms.DateField(required=False)

    def clean(self):
        datos = super().clean()
        hora_inicio = datos.get('hora_inicio')
        hora_fin = datos.get('hora_fin')

        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')

        if datos.get('recurrente'):
            if not datos.get('frecuencia'):
                self.add_error('frecuencia', 'Selecciona una frecuencia para la reserva recurrente.')
            if not datos.get('fecha_fin_recurrencia'):
                self.add_error('fecha_fin_recurrencia', 'Indica hasta cuándo se repite la reserva.')
            elif datos.get('fecha') and datos['fecha_fin_recurrencia'] < datos['fecha']:
                self.add_error(
                    'fecha_fin_recurrencia',
                    'Debe ser posterior a la fecha de la reserva.',
                )

        return datos


class BloqueoForm(forms.ModelForm):
    """Formulario para que el personal del club cree bloqueos de mantenimiento/eventos."""

    class Meta:
        model = Bloqueo
        fields = ['pista', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'motivo']
        widgets = {
            'pista': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
