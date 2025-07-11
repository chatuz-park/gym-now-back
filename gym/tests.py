from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from .models import Client, CustomUser

# Create your tests here.

class ClientUserCreationTest(TestCase):
    """Test para verificar que los clientes se crean con usuarios y roles correctos"""
    
    def test_client_creation_creates_user_with_correct_role(self):
        """Test que verifica que al crear un cliente se crea automáticamente un usuario con rol 'client'"""
        # Crear un cliente
        client = Client.objects.create(
            name="Juan Pérez",
            email="juan.perez@test.com",
            phone="+1234567890",
            birth_date=date(1990, 5, 15),
            weight=75.5,
            height=175.0,
            goals=["Perder peso", "Ganar músculo"],
            join_date=date.today(),
            subscription_type="premium"
        )
        
        # Verificar que se creó un usuario
        self.assertIsNotNone(client.user)
        self.assertEqual(client.user.email, "juan.perez@test.com")
        
        # Verificar que el username se generó correctamente
        self.assertTrue(client.user.username.startswith("juan.perez"))
        
        # Verificar que se creó un CustomUser con rol 'client'
        custom_user = CustomUser.objects.get(user=client.user)
        self.assertEqual(custom_user.role, 'client')
        
        # Verificar que la contraseña se generó correctamente
        expected_password = f"{client.age:02d}00"
        self.assertTrue(client.user.check_password(expected_password))
    
    def test_client_creation_with_existing_username(self):
        """Test que verifica que se maneja correctamente cuando el username ya existe"""
        # Crear un usuario existente
        existing_user = User.objects.create_user(
            username="juan.perez",
            email="existing@test.com",
            password="testpass"
        )
        
        # Crear un cliente con email que generaría el mismo username
        client = Client.objects.create(
            name="Juan Pérez",
            email="juan.perez@test.com",
            phone="+1234567890",
            birth_date=date(1990, 5, 15),
            weight=75.5,
            height=175.0,
            goals=["Perder peso"],
            join_date=date.today()
        )
        
        # Verificar que se generó un username único
        self.assertNotEqual(client.user.username, "juan.perez")
        self.assertTrue(client.user.username.startswith("juan.perez"))
        
        # Verificar que el rol es correcto
        custom_user = CustomUser.objects.get(user=client.user)
        self.assertEqual(custom_user.role, 'client')
    
    def test_client_with_existing_user(self):
        """Test que verifica que un cliente con usuario existente mantiene el rol correcto"""
        # Crear un usuario primero
        user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass"
        )
        
        # Obtener el CustomUser creado automáticamente y cambiar su rol
        custom_user = CustomUser.objects.get(user=user)
        custom_user.role = 'guest'
        custom_user.save()
        
        # Crear un cliente asignándole el usuario existente
        client = Client.objects.create(
            name="Test Client",
            email="test@test.com",
            phone="+1234567890",
            birth_date=date(1990, 5, 15),
            weight=75.5,
            height=175.0,
            goals=["Test goal"],
            join_date=date.today(),
            user=user
        )
        
        # Verificar que el rol se cambió a 'client'
        custom_user.refresh_from_db()
        self.assertEqual(custom_user.role, 'client')
    
    def test_password_generation(self):
        """Test que verifica que la contraseña se genera correctamente basada en la edad"""
        # Cliente de 25 años (nacido en 1999, 25 años en 2024)
        client_25 = Client.objects.create(
            name="Test 25",
            email="test25@test.com",
            phone="+1234567890",
            birth_date=date(1999, 1, 1),
            weight=70.0,
            height=170.0,
            goals=[],
            join_date=date.today()
        )
        
        # Cliente de 40 años (nacido en 1984, 40 años en 2024)
        client_40 = Client.objects.create(
            name="Test 40",
            email="test40@test.com",
            phone="+1234567890",
            birth_date=date(1984, 1, 1),
            weight=80.0,
            height=180.0,
            goals=[],
            join_date=date.today()
        )
        
        # Verificar que las contraseñas se generaron correctamente
        self.assertEqual(client_25.generate_default_password(), "2600")  # 26 años en 2024
        self.assertEqual(client_40.generate_default_password(), "4000")
        
        # Verificar que los usuarios pueden autenticarse con estas contraseñas
        self.assertTrue(client_25.user.check_password("2600"))
        self.assertTrue(client_40.user.check_password("4000"))

    def test_email_and_phone_uniqueness(self):
        """Test que verifica que el email y teléfono sean únicos"""
        # Crear un cliente
        client1 = Client.objects.create(
            name="Juan Pérez",
            email="juan.perez@test.com",
            phone="+1234567890",
            birth_date=date(1990, 5, 15),
            weight=75.5,
            height=175.0,
            goals=["Perder peso"],
            join_date=date.today()
        )
        
        # Intentar crear otro cliente con el mismo email
        with self.assertRaises(Exception):  # Puede ser ValidationError o IntegrityError
            client2 = Client.objects.create(
                name="Juan Pérez 2",
                email="juan.perez@test.com",  # Mismo email
                phone="+1234567891",
                birth_date=date(1990, 5, 15),
                weight=75.5,
                height=175.0,
                goals=["Perder peso"],
                join_date=date.today()
            )
        
        # Intentar crear otro cliente con el mismo teléfono
        with self.assertRaises(Exception):  # Puede ser ValidationError o IntegrityError
            client3 = Client.objects.create(
                name="Juan Pérez 3",
                email="juan.perez2@test.com",
                phone="+1234567890",  # Mismo teléfono
                birth_date=date(1990, 5, 15),
                weight=75.5,
                height=175.0,
                goals=["Perder peso"],
                join_date=date.today()
            )

    def test_username_is_email(self):
        """Test que verifica que el username sea el email completo"""
        client = Client.objects.create(
            name="María García",
            email="maria.garcia@test.com",
            phone="+1234567892",
            birth_date=date(1990, 5, 15),
            weight=75.5,
            height=175.0,
            goals=["Perder peso"],
            join_date=date.today()
        )
        
        # Verificar que el username sea el email completo
        self.assertEqual(client.user.username, "maria.garcia@test.com")


class ClientRoutineValidationTest(TestCase):
    """Test para verificar la validación de assigned_days en ClientRoutine"""
    
    def test_client_routine_assigned_days_validation(self):
        """Test que la validación de assigned_days funciona correctamente"""
        from .serializers import ClientRoutineSerializer
        from .models import Routine
        
        # Crear cliente y rutina para las pruebas
        client = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            phone="1234567890",
            birth_date=date(1990, 1, 1),
            weight=70.0,
            height=175.0,
            join_date=date(2023, 1, 1)
        )
        
        routine = Routine.objects.create(
            name="Test Routine",
            description="Test Description",
            frequency="weekly",
            days_per_week=3,
            duration=4
        )
        
        # Test 1: Objeto con valores booleanos válidos
        data = {
            'client_id': client.id,
            'routine_id': routine.id,
            'start_date': '2023-01-01',
            'assigned_days': {
                'monday': True,
                'wednesday': True,
                'friday': True,
                'tuesday': False,
                'thursday': False,
                'saturday': False,
                'sunday': False
            }
        }
        
        serializer = ClientRoutineSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['assigned_days'], ['monday', 'wednesday', 'friday'])
        
        # Test 2: Lista de días válida
        data['assigned_days'] = ['monday', 'wednesday', 'friday']
        serializer = ClientRoutineSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['assigned_days'], ['monday', 'wednesday', 'friday'])
        
        # Test 3: Día inválido en lista
        data['assigned_days'] = ['monday', 'invalid_day', 'friday']
        serializer = ClientRoutineSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('assigned_days', serializer.errors)
        
        # Test 4: Tipo de dato inválido
        data['assigned_days'] = "invalid_type"
        serializer = ClientRoutineSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('assigned_days', serializer.errors)
