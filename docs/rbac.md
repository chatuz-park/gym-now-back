# RBAC — GymNow Backend

Control de acceso por roles de tres niveles. El contrato OpenAPI es [`swagger.json`](../swagger.json): cada operación autenticada declara `security: Bearer` y `x-required-roles`.

La UI consume una copia en `gym-now/docs/swagger.json`. Tras cambiar permisos, regenerar y sincronizar (ver [Actualizar el contrato](#actualizar-el-contrato)).

## Roles

Viven en `CustomUser.role` (`gym/models.py`), un `OneToOne` sobre `django.contrib.auth.models.User` (`related_name='custom_profile'`).

| Valor | Quién | Alcance |
|-------|--------|---------|
| `owner` | Propietario / admin del gym | Todo, incluido borrar clientes y ver credenciales |
| `trainer` | Entrenador | Operación: clientes, catálogo, rutinas, progreso. No borra clientes ni ve credenciales |
| `client` | Socio con `client_profile` | Solo sus datos + lectura de catálogo |
| `guest` | Usuario sin perfil de cliente (o label equivalente) | Igual que `client` en la API |

Django `is_staff` / `is_superuser` solo aplica a `/admin/`. No hay rol `admin` en la API.

## Matriz de endpoints

Respuestas estándar: **401** sin JWT; **403** si el rol no alcanza o el recurso no es propio.

### Público (`AllowAny`)

- `POST /api/token/`
- `POST /api/token/refresh/`
- `POST /api/client-login/`

### Cualquier autenticado

- `GET /api/user-profile/` — fuente de verdad del rol (`UserProfile.role` enum)

### Solo owner

- `GET /api/users/`, `GET /api/users/{id}/`, `PATCH /api/users/{id}/` — listar usuarios y cambiar `role`
- `POST /api/plans/`, `PUT/PATCH /api/plans/{id}/`, `DELETE /api/plans/{id}/`
- `DELETE /api/clients/{id}/`
- `GET /api/clients/{id}/credentials/`
- `GET /api/clients/all_credentials/`

`default_password` en el serializer de `Client` solo se rellena si el request es owner; para el resto es `null`.

### Staff (`owner` + `trainer`)

- CRUD de clientes (salvo delete)
- `GET /api/clients/`, `GET /api/clients/statistics/`
- `GET /api/plans/`, `GET /api/plans/{id}/` — catálogo de planes para asignar a clientes
- Escritura de ejercicios, workouts, sets, rutinas, asignaciones, goals, progress
- `POST /api/exercises/{id}/upload_image/`
- `GET /api/routines/statistics/`

### Miembro (`client` + `guest`)

- `GET /api/clients/me/`
- Lectura/escritura **solo de recursos propios**: `GET /api/clients/{id}/` (403 si es otro), `progress`, `goals`, `routines`, `upload_profile_image`, `complete_workout`
- `GET /api/client-routines/` recortado a su cliente
- Lectura de catálogo (`/exercises/`, `/routines/`, `/workouts/`, sets) para renderizar la rutina asignada
- No lista todos los clientes ni crea ejercicios/rutinas

## Arquitectura

```
JWT Bearer
    → IsAuthenticated (default en REST_FRAMEWORK)
    → HasRole(*role_map[action])
    → IsSelfClient (solo en object_permission_actions)
    → get_queryset recorta listados de miembros
```

Archivos clave:

| Archivo | Rol |
|---------|-----|
| [`gym/permissions.py`](../gym/permissions.py) | `HasRole`, `IsSelfClient`, `RoleMapMixin`, helpers de rol |
| [`gym/schema.py`](../gym/schema.py) | Inspector drf-yasg: `Bearer`, `x-required-roles`, 401/403 |
| [`gym/views.py`](../gym/views.py) | `role_map` por ViewSet |
| [`gym/serializers.py`](../gym/serializers.py) | `UserProfileSerializer.role` (ChoiceField), `UserRoleAdminSerializer`, `GymTokenObtainPairSerializer` |
| [`gymnow_backend/settings.py`](../gymnow_backend/settings.py) | `DEFAULT_PERMISSION_CLASSES`, `SWAGGER_SETTINGS`, JWT |

### `role_map`

Cada ViewSet declara qué roles admite cada acción. El default seguro es staff. Ejemplo (`ClientViewSet`):

- `list` / `create` / `update` → staff
- `destroy` / `credentials` / `all_credentials` → owner
- `retrieve` / `me` / `progress` / `goals` / `routines` / `upload_profile_image` → todos los roles autenticados
- `object_permission_actions` aplica `IsSelfClient` (staff pasa; miembro solo su `Client`)

### JWT

`GymTokenObtainPairSerializer` añade al access token:

- `role` — valor de `custom_profile.role` (o `guest` si no hay perfil)
- `user_id`

El front puede leer el claim, pero la fuente de verdad sigue siendo `GET /api/user-profile/`.

## Asignación de roles

1. **API** (`UserViewSet`, solo owner): `GET /api/users/` lista usuarios; `PATCH /api/users/{id}/` cambia `role`. No crea ni borra cuentas ni fichas `Client`. Rechaza degradar al último `owner` (400).
2. **Django admin** → `Custom Users`: vía alternativa.
3. **Signals** (`gym/models.py`): al crear un `User` se crea `CustomUser` con default `client`. Al crear un `Client` sin usuario se crea el `User` y se fuerza `client`.
4. **`assign_user_roles`**: usuarios con `client_profile` → `client`; sin perfil → `guest`. **No pisa** `trainer` ni `owner`.

```bash
pipenv run python manage.py assign_user_roles
```

## Actualizar el contrato

El servidor debe estar corriendo.

```bash
cd gym-now-back
pipenv run python manage.py update_swagger
cp swagger.json ../gym-now/docs/swagger.json
```

Comprobar en el JSON:

- `securityDefinitions.Bearer`
- `UserProfile.properties.role.enum`
- `x-required-roles` en las operaciones autenticadas

## Tests

```bash
pipenv run python manage.py test gym.tests.RoleBasedAccessTest
```

Cubre 401 sin token, 403 de miembro en list/delete/otro cliente, 200 en `/clients/me/`, trainer sin delete/credenciales, owner con ambos, claim JWT, que `assign_user_roles` conserve staff, y la API de usuarios (403 de trainer/miembro, list/PATCH de owner, último owner).

## Fuera de alcance

- Crear o borrar usuarios por API
- Roles o permisos custom
- Diferenciar `guest` de `client` más allá del label
- Generación de tipos TypeScript desde Swagger
