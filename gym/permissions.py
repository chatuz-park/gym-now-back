from rest_framework.permissions import BasePermission

from .models import Client

ROLE_CLIENT = 'client'
ROLE_TRAINER = 'trainer'
ROLE_GUEST = 'guest'
ROLE_OWNER = 'owner'

ALL_ROLES = (ROLE_CLIENT, ROLE_TRAINER, ROLE_GUEST, ROLE_OWNER)
STAFF_ROLES = (ROLE_OWNER, ROLE_TRAINER)
MEMBER_ROLES = (ROLE_CLIENT, ROLE_GUEST)
OWNER_ROLES = (ROLE_OWNER,)


def get_user_role(user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return None
    profile = getattr(user, 'custom_profile', None)
    if profile is None:
        return None
    return profile.role


def is_staff_role(role):
    return role in STAFF_ROLES


def is_member_role(role):
    return role in MEMBER_ROLES


def is_owner_role(role):
    return role == ROLE_OWNER


def get_user_client(user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return None
    try:
        return user.client_profile
    except Client.DoesNotExist:
        return None


def get_related_client(obj):
    if isinstance(obj, Client):
        return obj
    client = getattr(obj, 'client', None)
    if client is not None:
        return client
    client_routine = getattr(obj, 'client_routine', None)
    if client_routine is not None:
        return getattr(client_routine, 'client', None)
    return None


class HasRole(BasePermission):
    """Permite el acceso si el rol del usuario está en la lista indicada."""

    message = 'No tienes permiso para realizar esta acción.'

    def __init__(self, *roles):
        super().__init__()
        self.allowed_roles = roles

    def has_permission(self, request, view):
        role = get_user_role(request.user)
        return bool(role and role in self.allowed_roles)


class IsSelfClient(BasePermission):
    """Staff: cualquier objeto. Miembro: solo recursos de su propio Client."""

    message = 'No tienes permiso para acceder a este recurso.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user)
        if is_staff_role(role):
            return True
        own_client = get_user_client(request.user)
        if own_client is None:
            return False
        related = get_related_client(obj)
        return related is not None and related.pk == own_client.pk


class RoleMapMixin:
    """Aplica role_map + chequeo de objeto propio en las acciones indicadas."""

    role_map = {}
    object_permission_actions = frozenset()

    def get_required_roles(self):
        action = getattr(self, 'action', None)
        if action in self.role_map:
            return self.role_map[action]
        return self.role_map.get('default', STAFF_ROLES)

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated

        roles = self.get_required_roles()
        permissions = [IsAuthenticated(), HasRole(*roles)]
        if getattr(self, 'action', None) in self.object_permission_actions:
            permissions.append(IsSelfClient())
        return permissions
