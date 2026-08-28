# Portal de Suscripciones — cifnoba.com

Portal web donde SOCAPS, SOFIPOS y SOFOMES se registran y suscriben para
acceder al sistema de reclutamiento con postulación conversacional Fast Apply.

## Ejecución

```bash
uvicorn portal.main:app --reload --port 8002
```

Para cargar datos de demostración:

```bash
python -m scripts.seed_portal
```

Usuarios de demo (contraseña: `demo1234`):

| Correo                            | Organización                | Plan         |
|-----------------------------------|-----------------------------|--------------|
| ana.garcia@cajapopularsur.mx      | Caja Popular del Sur        | Profesional  |
| carlos.mendoza@finbajio.com       | Financiera del Bajío Popular| Empresarial  |
| mftorres@creditoexpress.mx        | Crédito Express MX          | Básico       |

## Variables de entorno

| Variable              | Descripción                                       | Por omisión           |
|-----------------------|---------------------------------------------------|-----------------------|
| `PORTAL_DATABASE_URL` | Cadena de conexión SQLAlchemy                     | `sqlite:///./portal.db`|

## Estructura de archivos

```
portal/
├── main.py              # App FastAPI, landing page
├── database.py          # Motor SQLAlchemy y sesión
├── models.py            # Organizacion, UsuarioPortal, SesionPortal, Suscripcion
├── auth.py              # Hashing PBKDF2, sesiones por cookie
├── plantillas.py        # Jinja2 con filtros y globales
├── routers/
│   ├── auth.py          # /registro, /login, /logout
│   └── panel.py         # /panel, /panel/suscripcion, /panel/organizacion
├── templates/
│   ├── landing.html     # Página pública de cifnoba.com
│   ├── registro.html    # Formulario de registro de organizaciones
│   ├── login.html       # Inicio de sesión
│   ├── panel.html       # Dashboard post-login
│   ├── suscripcion.html # Gestión de suscripción y cambio de plan
│   └── organizacion.html# Edición de datos de la organización
└── static/
    └── portal.css       # Estilos del portal
```

## Rutas

### Públicas

| Ruta        | Método | Descripción                          |
|-------------|--------|--------------------------------------|
| `/`         | GET    | Landing page con planes y beneficios |
| `/registro` | GET    | Formulario de registro               |
| `/registro` | POST   | Crear organización + usuario + suscripción |
| `/login`    | GET    | Formulario de inicio de sesión       |
| `/login`    | POST   | Autenticar usuario                   |
| `/logout`   | GET    | Cerrar sesión                        |

### Protegidas (requieren login)

| Ruta                       | Método | Descripción                    |
|----------------------------|--------|--------------------------------|
| `/panel`                   | GET    | Dashboard de la organización   |
| `/panel/suscripcion`       | GET    | Detalle de suscripción activa  |
| `/panel/suscripcion/cambiar`| POST  | Cambiar de plan                |
| `/panel/organizacion`      | GET    | Formulario de datos de la org  |
| `/panel/organizacion`      | POST   | Guardar cambios de la org      |

## Planes de suscripción

| Plan          | Precio/mes | Vacantes | Usuarios | QR | IA |
|---------------|-----------|----------|----------|----|----|
| Básico        | $2,499    | 3        | 1        | No | No |
| Profesional   | $4,999    | 10       | 5        | Sí | No |
| Empresarial   | $9,999    | Ilimitadas| Ilimitados| Sí| Sí|

Todos los planes incluyen 14 días de prueba gratuita.

## Autenticación

- Contraseñas hasheadas con PBKDF2-SHA256 (260,000 iteraciones)
- Sesiones por cookie (`cifnoba_session`) con token aleatorio
- Duración de sesión: 30 días
- Sesiones almacenadas en base de datos (tabla `sesiones_portal`)

## Modelos de datos

- **Organizacion**: datos de la institución financiera (nombre, RFC, tipo, contacto)
- **UsuarioPortal**: cuenta de acceso vinculada a una organización (email, password, rol)
- **SesionPortal**: token de sesión con expiración
- **Suscripcion**: plan contratado con estado (prueba/activa/vencida/cancelada)

## Pruebas

```bash
python -m pytest tests/test_portal.py -v
```

21 pruebas cubriendo: landing page, registro, validaciones (RFC duplicado, email
duplicado, contraseña corta), login/logout, panel protegido, suscripción,
cambio de plan, edición de organización y hashing de contraseñas.
