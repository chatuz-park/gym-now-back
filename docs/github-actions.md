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