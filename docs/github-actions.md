# GitHub Actions Self-Hosted Runner Setup

## Configuración del Runner

### 1. Ejecutar el script de instalación

```bash
./scripts/setup-runner.sh
```

### 2. Configurar el runner

1. Ve a tu repositorio en GitHub: `Settings > Actions > Runners > New self-hosted runner`
2. Copia el token de registro
3. Ejecuta en tu servidor:

```bash
cd ~/actions-runner
./config.sh --url https://github.com/TU_USUARIO/gym-now-back --token TU_TOKEN
```

### 3. Instalar como servicio

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

## Configuración de Variables de Entorno

### Método 1: GitHub Secrets (Recomendado)

Configura estos secrets en GitHub (`Settings > Secrets and variables > Actions`):

#### Secrets requeridos:
- `SECRET_KEY`: Clave secreta de Django
- `ALLOWED_HOSTS`: Dominios permitidos (ej: `mydomain.com,192.168.1.100`)
- `DB_NAME`: Nombre de la base de datos
- `DB_USER`: Usuario de PostgreSQL
- `DB_PASSWORD`: Contraseña de PostgreSQL
- `DB_HOST`: Host de la base de datos
- `DB_PORT`: Puerto de PostgreSQL (normalmente 5432)
- `AWS_ACCESS_KEY_ID`: AWS Access Key
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Key
- `AWS_S3_REGION_NAME`: Región de AWS
- `AWS_STORAGE_BUCKET_NAME`: Nombre del bucket S3
- `AWS_S3_CUSTOM_DOMAIN`: Dominio personalizado de S3

### Método 2: Archivo .env en servidor

1. Copia `.env.production` al servidor:
```bash
scp .env.production user@server:/path/to/gym-now-back/.env
```

2. Edita las variables en el servidor:
```bash
nano /path/to/gym-now-back/.env
```

### Método 3: Variables de entorno del sistema

```bash
# En el servidor, agregar a ~/.bashrc o /etc/environment
export SECRET_KEY="your-secret-key"
export DB_PASSWORD="your-db-password"
# etc...
```

## Secrets Requeridos

Configura estos secrets en tu repositorio (`Settings > Secrets and variables > Actions`):

### Deployment
- `DEPLOY_PATH`: Ruta donde está el proyecto en producción (ej: `/home/user/gym-now-back`)

### Docker (opcional)
- `DOCKER_USERNAME`: Usuario de Docker Hub
- `DOCKER_PASSWORD`: Password/Token de Docker Hub

## Workflows Disponibles

### CI/CD Pipeline (`.github/workflows/ci-cd.yml`)
- **Trigger**: Push a `main`/`develop`, PR a `main`
- **Funciones**:
  - Tests con PostgreSQL
  - Deploy automático a producción (solo `main`)

### Docker Build (`.github/workflows/docker.yml`)
- **Trigger**: Push a `main`, tags `v*`
- **Funciones**:
  - Build y push de imagen Docker
  - Versionado automático

### Security Scan (`.github/workflows/security.yml`)
- **Trigger**: Push, PR, schedule semanal
- **Funciones**:
  - Análisis de seguridad con Bandit
  - Verificación de dependencias con Safety

## Configuración del Servidor

### Requisitos mínimos
- Ubuntu 20.04+ / Debian 11+
- 2GB RAM
- 20GB almacenamiento
- Docker y Docker Compose
- Python 3.11+
- Git

### Estructura recomendada
```
/home/deploy/
├── gym-now-back/          # Repositorio clonado
├── actions-runner/        # GitHub Actions runner
└── .env                   # Variables de producción
```

## Comandos útiles

### Gestión del runner
```bash
# Ver estado
sudo systemctl status actions.runner.*

# Reiniciar
sudo ./svc.sh stop
sudo ./svc.sh start

# Ver logs
journalctl -u actions.runner.* -f
```

### Deployment manual
```bash
cd /path/to/gym-now-back
git pull origin main
docker-compose down
docker-compose up -d --build
docker-compose exec web python manage.py migrate
```