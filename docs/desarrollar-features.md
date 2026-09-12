# Desarrollar features en el backend

Cómo añadir o cambiar cualquier cosa en la API: un modelo nuevo, un campo, un filtro, una acción o un comando. El contrato con el front es OpenAPI (`swagger.json`) más `x-required-roles`. La UI oculta botones; **autoriza el API**.

Detalle de roles y JWT: [rbac.md](rbac.md). Guía del frontend: `gym-now/docs/desarrollar-features.md`. Arranque local: [GETTING_STARTED.md](../../docs/GETTING_STARTED.md).

## 1. Acotar el cambio

Antes de abrir archivos, responde:

1. **¿Qué recurso es?** ¿Modelo nuevo, campo en uno existente, acción sobre un ViewSet, o comando/management?
2. **¿Quién lo llama?** `STAFF_ROLES`, `OWNER_ROLES`, `MEMBER_ROLES`, `ALL_ROLES` o `AllowAny`. El default de `RoleMapMixin` es staff.
3. **¿El miembro ve solo lo suyo?** Si sí, la acción entra en `object_permission_actions` (`IsSelfClient`) y, si lista, `get_queryset` recorta.
4. **¿Qué escribe el cliente?** Lista campos de lectura y de escritura. No expongas el modelo entero si el front solo manda uno o dos.
5. **¿Qué debe fallar con 400?** Unicidad, transiciones, “no borrar el último X”, fechas, etc.

No hay tablas de permisos. Un permiso nuevo es una clave en `role_map` (o `required_roles` en una vista función). Los roles siguen siendo `owner | trainer | client | guest`.

## 2. Dónde vive cada pieza

Una app: `gym`. No crees otra Django app para un feature.

| Si el feature… | Archivo |
| --- | --- |
| Cambia el esquema | [`gym/models.py`](../gym/models.py) + migración |
| Valida o transforma payload | [`gym/serializers.py`](../gym/serializers.py) |
| Filtra / busca / ordena listados | [`gym/filters.py`](../gym/filters.py) |
| Expone HTTP | [`gym/views.py`](../gym/views.py) |
| Cuelga la URL | [`gym/urls.py`](../gym/urls.py) (`/api/…`) |
| Se edita en `/admin/` | [`gym/admin.py`](../gym/admin.py) |
| Es lógica reusable (S3, etc.) | [`gym/services.py`](../gym/services.py) |
| Es un job o seeder | `gym/management/commands/` |
| Cambia quién entra | [`gym/permissions.py`](../gym/permissions.py) y [rbac.md](rbac.md) |
| Lo consume el front | `swagger.json` → `gym-now/docs/swagger.json` |

Paginación global: `PageNumberPagination`, 20 por página (`?page=`). JWT en `Authorization: Bearer <access>`.

## 3. Orden de trabajo

Sigue este orden aunque el feature sea chico. Si un paso no aplica, sáltalo.

### Modelo y migración

Solo si cambia la BD.

```bash
pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
```

Convenciones ya usadas:

- `related_name` explícito en FKs / OneToOne (`client_profile`, `custom_profile`).
- Signals en `models.py` cuando un alta debe crear algo más (usuario al crear `Client`, `CustomUser` al crear `User`).
- `clean()` / `save()` para unicidad de negocio que el admin también debe respetar.
- No uses Django `is_staff` / `is_superuser` para autorizar la API.

Si el feature no toca tablas, no generes migración vacía.

### Serializer

- `ModelSerializer` para CRUD del recurso. Serializer aparte (`*CreateSerializer`, upload, etc.) cuando el write no es el mismo que el read.
- `read_only_fields` para ids, timestamps y todo lo que el cliente no debe pisar.
- Nested `source='relacion.campo'`: en `validate()` el valor llega anidado (`attrs['relacion']['campo']`). En `update()`, si usas `select_related`, reasigna el related en `instance` después de guardar; si no, el 200 puede devolver el valor viejo.
- Errores que el front muestra en toast: `raise serializers.ValidationError({'detail': '…'})`. El cliente lee `detail`, `error` o `message`. Un error solo de campo (`{'email': ['…']}`) no llega ahí.

### Filtros

`FilterSet` + `DjangoFilterBackend` + `OrderingFilter`. `search` suele ser un `CharFilter(method='search_filter')` con `Q(...)`.

```python
class RecursoFilter(filters.FilterSet):
    search = django_filters.CharFilter(method='search_filter', label='Buscar')

    class Meta:
        model = Recurso
        fields = {'estado': ['exact']}

    def search_filter(self, queryset, name, value):
        return queryset.filter(Q(nombre__icontains=value) | Q(email__icontains=value))
```

`ChoiceFilter` lleva **tuplas** `(valor, label)` (`MiModelo.CHOICES`). Una lista de strings revienta en `is_valid()` con 500, no con 400.

Declara `ordering_fields` y `ordering` en el ViewSet. Documenta `search`, `ordering` y `page` en `@swagger_auto_schema` del `list`.

### Vista

Tres formas, de más a menos habitual:

**CRUD de un modelo** — `RoleMapMixin` + `ModelViewSet` (clientes, ejercicios, rutinas).

**Recurso parcial** — mixins sueltos + `GenericViewSet` + `http_method_names` si no hay create/delete.

**Acción extra** — `@action` en el ViewSet que ya posee el objeto (`progress`, `credentials`, `complete_workout`). Pon esa acción en `role_map`. Si es de un socio sobre *su* cliente, también en `object_permission_actions`.

```python
class RecursoViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = Recurso.objects.all()
    serializer_class = RecursoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RecursoFilter
    ordering_fields = ['nombre', 'creado']
    ordering = ['-creado']
    role_map = {
        'list': STAFF_ROLES,
        'create': STAFF_ROLES,
        'retrieve': ALL_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': OWNER_ROLES,
        'default': STAFF_ROLES,
    }
    object_permission_actions = frozenset({'retrieve'})
```

Vista función (`@api_view`): asigna `mi_vista.cls.required_roles = …` para que Swagger emita `x-required-roles`. Público: `AllowAny` (login, refresh).

En `get_queryset`, `select_related` / `prefetch_related` de lo que serializas. OneToOne ausente (`user.client_profile`) lanza `DoesNotExist`; no asumas que existe.

### URL y admin

```python
router.register(r'recursos', RecursoViewSet)
```

Queda `/api/recursos/` y `/api/recursos/{id}/`. Las `@action` cuelgan de ahí (`/api/recursos/{id}/progress/`).

Si el modelo se gestiona a mano, regístralo en admin (`list_display`, `search_fields`, `list_filter`).

### Tests

Añade casos en [`gym/tests.py`](../gym/tests.py). Para auth y roles, reusa `RoleBasedAccessTest` (`_make_user`, `_make_client`, `_auth`). Para reglas del modelo o del serializer, un `TestCase` propio está bien.

Por cada operación HTTP nueva, como mínimo:

| Caso | Esperado |
| --- | --- |
| Sin token | 401 |
| Rol fuera de `role_map` | 403 |
| Rol permitido | 200 / 201 / 204 |
| Recurso de otro socio (si aplica) | 403 |
| Regla de negocio | 400 y la BD no cambia |
| `?search=` / filtro / `?ordering=` | 200 y el recorte correcto |

```bash
pipenv run python manage.py test gym.tests
# o una clase:
pipenv run python manage.py test gym.tests.RoleBasedAccessTest
```

El JWT de test sale de `RefreshToken.for_user(user).access_token`. Autoriza `custom_profile.role`, no `is_staff`.

Un `list` 200 no prueba filtros: pega el query param.

### Contrato y docs

El servidor tiene que estar corriendo. `--force` escribe un Swagger vacío.

```bash
cd gym-now-back
pipenv run python manage.py update_swagger
cp swagger.json ../gym-now/docs/swagger.json
```

En ambos JSON: path nuevo, `Bearer` si no es público, `x-required-roles` = `role_map` de esa acción, `definitions` del serializer.

Si cambió quién entra o hay path nuevo, actualiza [rbac.md](rbac.md). El front debe usar el mismo grupo en `allowedRoles` / helpers de `gym-now/src/lib/rbac.ts`.

HasRole lee la BD, no el claim JWT. Un cambio de rol vale en el siguiente request; no hace falta invalidar tokens.

## 4. Checklist

- [ ] Migración aplicada (solo si cambió el esquema)
- [ ] Serializer: write-set mínimo, `detail` en errores de negocio
- [ ] `role_map` o `required_roles` en **cada** acción (incluye `@action`)
- [ ] `object_permission_actions` + queryset recortado si un miembro toca lo propio
- [ ] FilterSet: `search`, choices en tuplas, `ordering` declarado
- [ ] Ruta en el router (o `path` si es función)
- [ ] Admin si el dato se edita a mano
- [ ] Tests: 401 / 403 / feliz / 400 / filtros
- [ ] Swagger regenerado y copiado al front
- [ ] [rbac.md](rbac.md) si cambió la matriz

## 5. Errores que se repiten

- **Acción nueva sin clave en `role_map`.** Cae al default (staff). Un socio recibe 403 “inexplicable” o Swagger documenta mal.
- **Related cacheado.** Tras guardar un OneToOne, reasigna en `instance` o el 200 miente.
- **Choices como lista de strings.** 500 en el listado filtrado.
- **`__all__` en el serializer de write.** El front (o un cliente) puede pisar campos que no pensaste.
- **Probar solo el happy path.** Sin 403 y sin query params el permiso y el filtro no están cubiertos.
- **Swagger desfasado.** El front copia `gym-now/docs/swagger.json`; si no lo actualizas, el contrato miente.
- **Confundir admin de Django con rol de la API.** `createsuperuser` no te hace `owner`.
