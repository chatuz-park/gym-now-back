from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from rest_framework.permissions import AllowAny

from .permissions import ALL_ROLES


class RoleSwaggerAutoSchema(SwaggerAutoSchema):
    """Documenta Bearer JWT, x-required-roles y respuestas 401/403."""

    def get_security(self):
        if self._is_public():
            return []
        return [{'Bearer': []}]

    def get_operation(self, operation_keys):
        operation = super().get_operation(operation_keys)
        if operation is None:
            return None

        roles = self._required_roles()
        if roles:
            operation['x-required-roles'] = list(roles)

        if not self._is_public():
            responses = operation.setdefault('responses', {})
            if '401' not in responses:
                responses['401'] = openapi.Response(
                    description='Authentication credentials were not provided.'
                )
            if '403' not in responses:
                responses['403'] = openapi.Response(
                    description='You do not have permission to perform this action.'
                )

        return operation

    def _permission_instances(self):
        try:
            return list(self.view.get_permissions())
        except Exception:
            classes = getattr(self.view, 'permission_classes', []) or []
            instances = []
            for cls in classes:
                try:
                    instances.append(cls() if isinstance(cls, type) else cls)
                except TypeError:
                    continue
            return instances

    def _is_public(self):
        perms = self._permission_instances()
        return bool(perms) and all(isinstance(perm, AllowAny) for perm in perms)

    def _required_roles(self):
        if self._is_public():
            return None

        view = self.view
        action = getattr(view, 'action', None)
        role_map = getattr(view, 'role_map', None)
        if isinstance(role_map, dict):
            if action in role_map:
                return role_map[action]
            if 'default' in role_map:
                return role_map['default']

        required = getattr(view, 'required_roles', None)
        if required:
            return required

        return ALL_ROLES
