from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gym.models import CustomUser, Client

class Command(BaseCommand):
    help = 'Asigna roles a usuarios existentes basado en si tienen perfil de cliente o no'

    def handle(self, *args, **options):
        self.stdout.write('Asignando roles a usuarios existentes...')
        
        # Obtener todos los usuarios
        users = User.objects.all()
        
        for user in users:
            # Verificar si ya tiene un CustomUser
            custom_user, created = CustomUser.objects.get_or_create(user=user)
            
            # Determinar el rol basado en si tiene perfil de cliente
            if hasattr(user, 'client_profile') and user.client_profile is not None:
                role = 'client'
            else:
                # Para usuarios sin perfil de cliente, asignar 'guest' por defecto
                # Los administradores pueden ser cambiados manualmente a 'owner' o 'trainer'
                role = 'guest'
            
            # Actualizar el rol si es diferente
            if custom_user.role != role:
                custom_user.role = role
                custom_user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario {user.username}: rol asignado como "{role}"')
                )
            else:
                self.stdout.write(
                    f'Usuario {user.username}: ya tiene rol "{role}"'
                )
        
        self.stdout.write(
            self.style.SUCCESS('Proceso completado. Usa el admin de Django para ajustar roles específicos.')
        ) 