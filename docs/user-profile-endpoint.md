# Endpoint de Información del Usuario

## Descripción
Este endpoint permite obtener la información básica del usuario autenticado basado en el token de sesión JWT, incluyendo su rol en el sistema.

## URL
```
GET /api/user-profile/
```

## Autenticación
Requiere autenticación mediante token JWT. El token debe incluirse en el header de la petición:

```
Authorization: Bearer <token>
```

## Respuesta Exitosa (200 OK)

### Respuesta de ejemplo:
```json
{
    "id": 1,
    "username": "juan.perez",
    "email": "juan.perez@example.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "date_joined": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-20T14:45:00Z",
    "role": "client"
}
```

### Otros roles posibles:
```json
{
    "id": 2,
    "username": "trainer1",
    "email": "trainer1@example.com",
    "first_name": "Carlos",
    "last_name": "García",
    "date_joined": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-20T15:00:00Z",
    "role": "trainer"
}
```

## Respuesta de Error (401 Unauthorized)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

## Respuesta de Error (500 Internal Server Error)
```json
{
    "error": "Error al obtener información del usuario: <mensaje de error>"
}
```

## Campos de Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | integer | ID único del usuario |
| `username` | string | Nombre de usuario |
| `email` | string | Correo electrónico |
| `first_name` | string | Nombre |
| `last_name` | string | Apellido |
| `date_joined` | datetime | Fecha de registro |
| `last_login` | datetime | Último inicio de sesión |
| `role` | string | Rol del usuario en el sistema (client, trainer, guest, owner) |

## Ejemplo de Uso con cURL

```bash
curl -X GET \
  http://localhost:8000/api/user-profile/ \
  -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...' \
  -H 'Content-Type: application/json'
```

## Ejemplo de Uso con JavaScript (Fetch)

```javascript
const token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...';

fetch('/api/user-profile/', {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => {
    console.log('Información del usuario:', data);
    console.log('Rol del usuario:', data.role);
})
.catch(error => {
    console.error('Error:', error);
});
```

## Roles Disponibles

- **client**: Usuarios que tienen perfil de cliente en el gimnasio
- **trainer**: Entrenadores del gimnasio
- **guest**: Usuarios invitados o sin permisos específicos
- **owner**: Propietarios o administradores del gimnasio

## Notas Importantes

1. **Autenticación Requerida**: Este endpoint requiere que el usuario esté autenticado mediante token JWT.

2. **Información Básica**: Solo devuelve información básica del usuario y su rol, sin incluir el perfil de cliente.

3. **Seguridad**: Solo devuelve información del usuario autenticado, no permite acceder a información de otros usuarios.

4. **Gestión de Roles**: Los roles se pueden gestionar desde el admin de Django o mediante comandos de gestión.

5. **Rol por Defecto**: Los usuarios nuevos reciben el rol 'client' por defecto si tienen perfil de cliente, o 'guest' en caso contrario. 