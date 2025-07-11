from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gym.models import CustomUser, Client

class Command(BaseCommand):
    help = 'Asegura que todos los clientes tengan usuarios con rol client y contraseña por defecto'

    def handle(self, *args, **options):
        self.stdout.write('Verificando que todos los clientes tengan usuarios con rol correcto...')
        
        # Obtener todos los clientes
        clients = Client.objects.all()
        
        for client in clients:
            self.stdout.write(f'Procesando cliente: {client.name} ({client.email})')
            
            # Verificar si el cliente tiene usuario
            if not client.user:
                self.stdout.write(f'  - Cliente sin usuario, creando...')
                
                # Usar el email completo como username
                username = client.email
                base_username = username
                counter = 1
                
                # Asegurar que el username sea único
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Crear el usuario con la contraseña generada
                password = client.generate_default_password()
                user = User.objects.create_user(
                    username=username,
                    email=client.email,
                    password=password,
                    first_name=client.name.split()[0] if client.name else '',
                    last_name=' '.join(client.name.split()[1:]) if len(client.name.split()) > 1 else ''
                )
                
                # Asignar el usuario al cliente
                client.user = user
                client.save(update_fields=['user'])
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Usuario creado: {username} con contraseña: {password}')
                )
            else:
                self.stdout.write(f'  - Cliente ya tiene usuario: {client.user.username}')
            
            # Verificar que el CustomUser tenga rol 'client'
            if client.user:
                custom_user, created = CustomUser.objects.get_or_create(user=client.user)
                if custom_user.role != 'client':
                    old_role = custom_user.role
                    custom_user.role = 'client'
                    custom_user.save()
                    self.stdout.write(
                        self.style.WARNING(f'  - Rol cambiado de "{old_role}" a "client"')
                    )
                else:
                    self.stdout.write(f'  - Rol correcto: client')
        
        self.stdout.write(
            self.style.SUCCESS('Proceso completado. Todos los clientes tienen usuarios con rol correcto.')
        ) 