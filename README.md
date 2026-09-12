# GymNow Backend API

Backend completo para gestión de gimnasio desarrollado con Django REST Framework, PostgreSQL y JWT authentication.

## 🚀 Características

- **API REST completa** con ViewSets para todos los modelos
- **Autenticación JWT** con tokens de acceso y refresh
- **Documentación Swagger** automática
- **Filtros y búsquedas** avanzadas
- **Admin de Django** configurado
- **Variables de entorno** con python-dotenv
- **Base de datos PostgreSQL**
- **Datos iniciales** con seeder personalizado
- **Actualización automática** de documentación Swagger
- **CORS configurado** para desarrollo frontend

## 📋 Modelos Disponibles

- **Client** - Clientes del gimnasio
- **Exercise** - Ejercicios disponibles
- **Workout** - Rutinas de entrenamiento
- **WorkoutSet** - Series de ejercicios
- **Routine** - Programas de entrenamiento
- **ClientRoutine** - Asignación cliente-rutina
- **RoutineProgress** - Progreso de rutinas
- **ProgressMetrics** - Métricas de progreso
- **Goal** - Objetivos de los clientes

## 🛠️ Instalación

### Prerrequisitos

- Python 3.11+
- PostgreSQL
- pipenv

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd gym-now-back
```

### 2. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y configura tus variables:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
# Django Settings
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=gymnow_db
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password_postgres
DB_HOST=localhost
DB_PORT=5432

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
```

### 3. Crear base de datos PostgreSQL

```sql
CREATE DATABASE gymnow_db;
CREATE USER tu_usuario_postgres WITH PASSWORD 'tu_password_postgres';
GRANT ALL PRIVILEGES ON DATABASE gymnow_db TO tu_usuario_postgres;
```

### 4. Instalar dependencias

```bash
pipenv install
```

### 5. Aplicar migraciones

```bash
pipenv run python manage.py migrate
```

### 6. Poblar datos iniciales (Opcional)

```bash
pipenv run python manage.py seed_data
```

Este comando creará:
- **5 ejercicios** (Sentadillas, Press de Banca, Peso Muerto, Flexiones, Plancha)
- **3 workouts** (Fuerza Piernas, Fuerza Tren Superior, Funcional)
- **3 rutinas** (Principiante, Intermedia, Avanzada)
- **3 clientes** con datos completos
- **Métricas de progreso** y **objetivos** de ejemplo

### 7. Crear superusuario (opcional)

```bash
pipenv run python manage.py createsuperuser
```

### 8. Ejecutar el servidor

```bash
pipenv run python manage.py runserver
```

## 🌐 URLs de Acceso

- **API Root:** http://localhost:8000/api/
- **Swagger UI:** http://localhost:8000/swagger/
- **ReDoc:** http://localhost:8000/redoc/
- **Admin Django:** http://localhost:8000/admin/

## 🔧 Configuración de CORS

El backend está configurado para permitir peticiones desde aplicaciones frontend en desarrollo:

### Orígenes Permitidos

- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (React default)
- `http://localhost:8080` (Vue default)
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:8080`

### Headers Permitidos

- `authorization` (para JWT tokens)
- `content-type`
- `accept`
- `origin`
- `user-agent`
- `x-csrftoken`
- `x-requested-with`

### Métodos HTTP Permitidos

- `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`

### Solución de Problemas de CORS

Si tienes problemas de CORS desde tu frontend:

1. **Verificar que el servidor esté ejecutándose:**
   ```bash
   pipenv run python manage.py runserver
   ```

2. **Probar la configuración CORS:**
   ```bash
   curl -X OPTIONS http://localhost:8000/api/exercises/ \
     -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: authorization,content-type" \
     -v
   ```

3. **Verificar headers en respuesta:**
   - `access-control-allow-origin: http://localhost:5173`
   - `access-control-allow-credentials: true`
   - `access-control-allow-headers: accept, authorization, content-type, ...`
   - `access-control-allow-methods: DELETE, GET, OPTIONS, PATCH, POST, PUT`

4. **Si necesitas agregar más orígenes**, edita `gymnow_backend/settings.py`:
   ```python
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:5173",
       "http://tu-nuevo-origen:puerto",
   ]
   ```

## 📚 Documentación de la API

- [docs/rbac.md](docs/rbac.md) — roles, matriz de endpoints, JWT y cómo regenerar Swagger
- [docs/desarrollar-features.md](docs/desarrollar-features.md) — cómo desarrollar cualquier feature (modelo, API, tests, Swagger)
- [docs/user-profile-endpoint.md](docs/user-profile-endpoint.md) — `GET /api/user-profile/`

### Actualizar Swagger JSON

Para actualizar automáticamente la documentación cuando hagas cambios:

```bash
# Actualización básica
pipenv run python manage.py update_swagger

# Con opciones personalizadas
pipenv run python manage.py update_swagger --host=localhost:8000 --protocol=https --output=api-docs.json

# Forzar actualización (crea archivo vacío si el servidor no está ejecutándose)
pipenv run python manage.py update_swagger --force
```

**Opciones disponibles:**
- `--host`: Host y puerto del servidor (default: localhost:8000)
- `--protocol`: Protocolo a usar (default: http)
- `--output`: Archivo de salida (default: swagger.json)
- `--force`: Forzar actualización incluso si el servidor no está ejecutándose

### Exportar Swagger JSON (Método manual)

Para integrar la documentación en tu frontend:

```bash
curl -s http://localhost:8000/swagger/?format=openapi > swagger.json
```

El archivo `swagger.json` contiene toda la especificación de la API en formato OpenAPI 2.0.

### Endpoints Principales

#### Autenticación
- `POST /api/token/` - Obtener token JWT
- `POST /api/token/refresh/` - Renovar token

#### Clientes
- `GET/POST /api/clients/` - Listar/Crear clientes
- `GET/PUT/DELETE /api/clients/{id}/` - Obtener/Actualizar/Eliminar cliente
- `GET /api/clients/{id}/progress/` - Progreso del cliente
- `GET /api/clients/{id}/goals/` - Objetivos del cliente
- `GET /api/clients/{id}/routines/` - Rutinas asignadas

#### Ejercicios
- `GET/POST /api/exercises/` - Listar/Crear ejercicios
- `GET /api/exercises/by_difficulty/` - Por nivel de dificultad
- `GET /api/exercises/by_muscle_group/` - Por grupo muscular

#### Rutinas
- `GET/POST /api/workouts/` - Listar/Crear workouts
- `GET /api/workouts/by_category/` - Por categoría
- `GET /api/workouts/{id}/sets/` - Sets de un workout

#### Programas
- `GET/POST /api/routines/` - Listar/Crear programas
- `GET /api/routines/by_frequency/` - Por frecuencia
- `GET /api/routines/{id}/workouts/` - Workouts de un programa

## 🔍 Filtros y Búsquedas

### Filtros Disponibles

- **Clientes:** `subscription_type`, `age`, `join_date`
- **Ejercicios:** `difficulty`
- **Workouts:** `difficulty`, `category`, `estimated_duration`
- **Rutinas:** `frequency`, `days_per_week`, `duration`
- **Objetivos:** `category`, `is_completed`, `deadline`

### Búsquedas

- **Clientes:** `name`, `email`, `phone`
- **Ejercicios:** `name`, `description`
- **Workouts:** `name`, `description`
- **Rutinas:** `name`, `description`
- **Objetivos:** `title`, `description`

### Ordenamiento

Todos los endpoints soportan ordenamiento por campos específicos usando el parámetro `ordering`.

## 🔐 Autenticación

### Obtener Token

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "tu_usuario", "password": "tu_password"}'
```

### Usar Token

```bash
curl -H "Authorization: Bearer <tu_token>" \
  http://localhost:8000/api/clients/
```

### Ejemplo desde Frontend (JavaScript)

```javascript
// Obtener token
const response = await fetch('http://localhost:8000/api/token/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'tu_usuario',
    password: 'tu_password'
  })
});

const data = await response.json();
const token = data.access;

// Usar token para peticiones autenticadas
const clientsResponse = await fetch('http://localhost:8000/api/clients/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
});
```

## 🛠️ Desarrollo

### Estructura del Proyecto

```
gym-now-back/
├── gym/                    # App principal
│   ├── models.py          # Modelos de datos
│   ├── serializers.py     # Serializers de la API
│   ├── views.py           # ViewSets
│   ├── urls.py            # URLs de la app
│   ├── admin.py           # Configuración del admin
│   └── management/        # Comandos personalizados
│       └── commands/
│           ├── seed_data.py      # Seeder de datos iniciales
│           └── update_swagger.py # Actualización de documentación
├── gymnow_backend/        # Configuración del proyecto
│   ├── settings.py        # Configuración Django
│   └── urls.py            # URLs principales
├── .env                   # Variables de entorno
├── swagger.json           # Documentación exportada
└── README.md              # Este archivo
```

### Comandos Útiles

```bash
# Crear migraciones
pipenv run python manage.py makemigrations

# Aplicar migraciones
pipenv run python manage.py migrate

# Poblar datos iniciales
pipenv run python manage.py seed_data

# Actualizar documentación Swagger
pipenv run python manage.py update_swagger

# Ejecutar tests
pipenv run python manage.py test

# Shell de Django
pipenv run python manage.py shell

# Crear superusuario
pipenv run python manage.py createsuperuser
```

### Flujo de Desarrollo

1. **Hacer cambios** en modelos, serializers o views
2. **Crear migraciones** si es necesario: `pipenv run python manage.py makemigrations`
3. **Aplicar migraciones**: `pipenv run python manage.py migrate`
4. **Actualizar documentación**: `pipenv run python manage.py update_swagger`
5. **Probar cambios** en la API

## 📦 Dependencias Principales

- **Django 5.2.4** - Framework web
- **Django REST Framework** - API REST
- **djangorestframework-simplejwt** - Autenticación JWT
- **drf-yasg** - Documentación Swagger
- **django-filter** - Filtros avanzados
- **django-cors-headers** - Manejo de CORS
- **psycopg2-binary** - Adaptador PostgreSQL
- **python-dotenv** - Variables de entorno
- **requests** - Cliente HTTP para actualización de Swagger

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia BSD. Ver el archivo `LICENSE` para más detalles.

## 📞 Contacto

- Email: contact@gymnow.com
- Proyecto: [https://github.com/tu-usuario/gym-now-back](https://github.com/tu-usuario/gym-now-back) 