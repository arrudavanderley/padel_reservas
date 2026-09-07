# 🎾 Reservas de pádel

Sistema de reservas de pistas de pádel hecho con **Django** y **SQLite**, sin
pasarela de pago. Permite ver la disponibilidad en un calendario, reservar
sin solapamientos, crear reservas recurrentes y gestionar todo desde el
panel de administración de Django.

Este README está escrito paso a paso, asumiendo que es la primera vez que
vas a ejecutar un proyecto Django desde una terminal. Cada comando lleva
una línea explicando qué hace.

## Qué incluye

- Calendario interactivo (FullCalendar) con la disponibilidad de todas las pistas.
- Reservas con validación automática de solapamiento (no se puede reservar
  una pista que ya está ocupada, ni sobre un bloqueo administrativo),
  reforzada con bloqueo de fila (`select_for_update`) para dos peticiones
  simultáneas sobre la misma pista.
- Reservas recurrentes (diaria, semanal o mensual) con un solo formulario.
- Límite configurable de reservas activas por usuario (5 por defecto).
- Email de confirmación y de cancelación al hacer o cancelar una reserva.
- Bloqueos de horas o días completos para mantenimiento o eventos.
- Panel de administración con filtros y acciones masivas (cancelar/confirmar
  varias reservas a la vez).
- Registro e inicio de sesión de usuarios con Django.
- El calendario se actualiza solo tras cada reserva, sin recargar la página.
- Datos de prueba listos para cargar (3 pistas y 2 usuarios).
- Tests automáticos de la lógica de validación.

## Antes de empezar

Necesitas tener instalado **Python 3.10 o superior**. Todo lo demás
(Django, etc.) se instala en los pasos de abajo.

Vas a usar una **terminal** (también llamada consola o línea de comandos):
una ventana donde escribes comandos de texto en vez de hacer clic. Como
trabajas con VS Code, la forma más cómoda es su terminal integrada: con la
carpeta del proyecto abierta, `Ver → Terminal` (o `Ctrl + ñ` / `` Ctrl + ` ``)
abre una terminal ya situada en esa carpeta, sin salir del editor. También
puedes usar una terminal aparte si lo prefieres:

- **Windows**: busca "PowerShell" o "símbolo del sistema" en el menú de inicio.
- **macOS**: busca "Terminal" con Spotlight (Cmd + Espacio).
- **Linux**: suele estar en el menú de aplicaciones como "Terminal".

Si prefieres no instalar nada en tu ordenador y trabajar directamente desde
el navegador, puedes abrir este mismo repositorio en **GitHub Codespaces**
(botón verde "Code" → pestaña "Codespaces" → "Create codespace"), que te da
una terminal ya lista dentro del navegador. Los pasos de abajo son los
mismos en ambos casos.

## Instalación paso a paso

Todos los comandos se escriben uno por uno, pulsando Intro después de cada
uno y esperando a que termine antes de escribir el siguiente.

**1. Descomprime el proyecto (si lo tienes en un .zip) y entra en su
carpeta desde la terminal.** Para "entrar" en una carpeta desde la
terminal se usa `cd` (change directory) seguido de la ruta; por ejemplo,
si la has descomprimido en el Escritorio:
```bash
cd Desktop/padel_reservas
```

**2. Crea un entorno virtual.** Es una copia aislada de Python solo para
este proyecto, para no mezclar sus dependencias con otras cosas de tu
ordenador:
```bash
python -m venv venv
```

**3. Activa el entorno virtual** (hay que repetir este paso cada vez que
abras una terminal nueva para trabajar en el proyecto):
```bash
# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```
Si ha funcionado, verás `(venv)` al principio de la línea de la terminal.

**4. Instala las dependencias del proyecto** (Django y python-dotenv):
```bash
pip install -r requirements.txt
```

**5. Crea tu archivo de variables de entorno** a partir del ejemplo
incluido:
```bash
# Windows:
copy .env.example .env

# macOS / Linux:
cp .env.example .env
```
Abre el archivo `.env` con cualquier editor de texto y cambia el valor de
`SECRET_KEY` por algo propio (no hace falta que sea complicado para
probarlo en tu ordenador, pero no debe ser el mismo con el que
compartas el proyecto públicamente).

**6. Crea la base de datos ejecutando las migraciones:**
```bash
python manage.py migrate
```
Esto crea el archivo `db.sqlite3` con todas las tablas que necesita el
proyecto (pistas, reservas, bloqueos, usuarios...).

**7. Carga los datos de prueba** (3 pistas y 2 usuarios de ejemplo):
```bash
python manage.py loaddata reservas_app/fixtures/datos_prueba.json
```

**8. Crea tu propio superusuario**, para poder entrar en `/admin/`:
```bash
python manage.py createsuperuser
```
Te pedirá un nombre de usuario, un email (opcional) y una contraseña.

**9. Arranca el servidor de desarrollo:**
```bash
python manage.py runserver
```

**10. Abre el navegador** en <http://127.0.0.1:8000/>. Para entrar en el
panel de administración, ve a <http://127.0.0.1:8000/admin/> con el
superusuario que has creado en el paso 8.

Para parar el servidor, vuelve a la terminal y pulsa `Ctrl + C`.

### Credenciales de prueba

Tras cargar los fixtures del paso 7, puedes iniciar sesión como un usuario
normal (no administrador) con cualquiera de estas dos cuentas:

| Usuario  | Contraseña   |
|----------|--------------|
| `ana`    | `padel1234`  |
| `carlos` | `padel1234`  |

Son cuentas de prueba pensadas solo para tu ordenador. Si vas a desplegar
el proyecto en un servidor real, elimínalas o cámbiales la contraseña
desde `/admin/`.

## Emails de confirmación y cancelación

Por defecto, `EMAIL_BACKEND` está puesto en modo "consola": en vez de
enviar un email de verdad, lo imprime en la misma terminal donde tengas
corriendo `python manage.py runserver`. Así puedes ver que la reserva
dispara el email correspondiente sin necesitar ninguna cuenta de correo.

Para enviar emails de verdad, abre tu `.env` y:
1. Cambia `EMAIL_BACKEND` a `django.core.mail.backends.smtp.EmailBackend`.
2. Rellena `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` y
   `DEFAULT_FROM_EMAIL` con los datos de tu proveedor (Gmail, un hosting,
   etc. — cada uno tiene sus propios valores; búscalos como "SMTP settings"
   del proveedor que uses).

Si el envío falla (por ejemplo, credenciales SMTP incorrectas), la reserva
se guarda igualmente: `fail_silently=True` hace que un fallo de correo
nunca impida completar la reserva.

## Cómo funciona la validación de solapamiento

Toda la lógica vive en una única función, `hay_solape()`, en
`reservas_app/models.py`. Dadas una pista, una fecha y una franja horaria,
comprueba dos cosas:

1. Si existe otra reserva confirmada de esa misma pista y fecha cuya franja
   se cruza con la nueva (una reserva cancelada no cuenta).
2. Si existe un bloqueo administrativo que cubra esa fecha y esa franja.

Dos franjas se consideran solapadas cuando una empieza antes de que la otra
termine, y viceversa. Con esa regla, una reserva que termina a las 11:00 no
choca con otra que empieza a las 11:00 (son contiguas, no solapadas).

Esta misma función se usa en dos sitios: en el modelo `Reserva` (para que
nunca se pueda guardar una reserva inválida, ni siquiera desde el panel de
administración) y en la vista `crear_reserva` (que la usa una vez por cada
fecha, antes de guardar nada, cuando la reserva es recurrente).

Como refuerzo extra, `crear_reserva` bloquea la fila de la `Pista`
implicada (`select_for_update()`) mientras comprueba y guarda, dentro de
una única transacción. En PostgreSQL o MySQL esto hace que dos peticiones
simultáneas sobre la misma pista se procesen una detrás de otra, cerrando
del todo la pequeña ventana entre comprobar y guardar. **En SQLite este
bloqueo no tiene efecto real** (SQLite no soporta bloqueo de filas: la
llamada no da error, pero tampoco bloquea nada), así que aquí sigue siendo
`hay_solape()` la que realmente protege. Si en el futuro migras a
PostgreSQL, el mismo código empieza a ofrecer la protección completa sin
cambiar nada.

## Decisiones de diseño

Algunas cosas no estaban especificadas al detalle y he tenido que decidir
un criterio. Aquí está el razonamiento, por si quieres cambiarlo:

- **El calendario es público, pero reservar requiere iniciar sesión.**
  Así cualquiera puede comprobar la disponibilidad antes de registrarse.
  Si prefieres que todo el sitio requiera login, añade `@login_required`
  a la vista `calendario` en `views.py`.
- **Cancelar una reserva es un cambio de estado, no un borrado.** Se
  conserva el historial completo en la base de datos; una reserva
  cancelada simplemente deja de contar para la validación de solapamiento.
- **Las reservas recurrentes tienen un límite de seguridad** (104
  ocurrencias, definido como `LIMITE_OCURRENCIAS_RECURRENCIA` en
  `views.py`) para que un despiste con las fechas no genere miles de filas.
- **Cada usuario puede tener como máximo 5 reservas activas a la vez**
  (`LIMITE_RESERVAS_ACTIVAS_POR_USUARIO` en `views.py`). Una reserva
  recurrente cuenta como varias. Cámbialo si 5 no encaja con tu club.
- **La zona horaria por defecto es `Europe/Madrid`** (en `settings.py`).
  Cámbiala si el club está en otro país.
- Los nombres de carpetas del enunciado original (`mi_proyecto`) se han
  sustituido por `padel_reservas`, un nombre más concreto para este
  proyecto en concreto.

## Estructura del proyecto

```
padel_reservas/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── padel_reservas/          # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── reservas_app/            # La aplicación en sí
    ├── models.py            # Pista, Perfil, Reserva, Bloqueo, hay_solape()
    ├── views.py             # Calendario, API de eventos, crear/cancelar reserva...
    ├── forms.py             # Formularios de registro, reserva y bloqueo
    ├── admin.py             # Panel de administración personalizado
    ├── urls.py
    ├── tests.py
    ├── fixtures/
    │   └── datos_prueba.json
    ├── templates/reservas/
    │   ├── base.html
    │   ├── calendario.html
    │   ├── login.html
    │   ├── registro.html
    │   └── bloqueos_lista.html
    └── static/reservas/
        ├── css/estilos.css
        └── js/calendario.js
```

## Ejecutar los tests

```bash
python manage.py test
```

Comprueban, entre otras cosas, que dos reservas no puedan solaparse, que
una reserva recurrente cree el número correcto de filas y que nadie pueda
cancelar la reserva de otra persona.

> **Nota:** este proyecto se ha escrito y revisado con cuidado, pero se ha
> desarrollado en un entorno sin acceso a internet para instalar Django, así
> que no ha sido posible ejecutar `python manage.py test` de verdad antes de
> entregártelo. Ejecuta este comando en tu ordenador nada más instalarlo:
> si algo falla, dime el mensaje de error exacto y lo corregimos.

## Subir el proyecto a GitHub

Tienes tres formas de hacerlo sin escribir comandos de `git` a mano:

**Opción A: desde VS Code (recomendada, ya que es tu editor).** Con la
carpeta del proyecto abierta, ve al icono de "Control de código fuente" en
la barra lateral izquierda y pulsa "Publicar en GitHub" ("Publish to
GitHub"). VS Code crea el repositorio por ti y respeta el `.gitignore`
automáticamente (no subirá `venv/`, `.env` ni `db.sqlite3`). La primera vez
te pedirá iniciar sesión con tu cuenta de GitHub.

**Opción B: GitHub Desktop.** Aplicación con interfaz gráfica, sin escribir
comandos, que también respeta el `.gitignore`. Se descarga desde
<https://desktop.github.com/>.

**Opción C: interfaz web de GitHub.** Crea un repositorio nuevo y usa
"Add file → Upload files", arrastrando la carpeta del proyecto.
**Importante:** aquí el `.gitignore` **no se respeta** (solo funciona con
`git` de verdad, como en las opciones A y B), así que antes de arrastrar la
carpeta, excluye a mano: la carpeta `venv/`, el archivo `db.sqlite3`, el
archivo `.env` y cualquier carpeta `__pycache__/`. Ninguno de ellos debe
subirse (el primero pesa mucho, y los otros dos contienen tu clave secreta
y tus datos locales).

## Ideas para seguir aprendiendo

Estas no están implementadas, pero encajan bien como siguiente paso:

- Una página de "Mis reservas" con el listado propio y opción de cancelar
  sin pasar por el calendario.
- Exportar las reservas propias a un archivo `.ics` para importarlas en
  Google Calendar o similar.
