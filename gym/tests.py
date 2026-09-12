from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from .models import Client, CustomUser, Exercise, Plan

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


class RoleBasedAccessTest(TestCase):
    """RBAC: 401 sin token, 403 por rol, y acceso a recursos propios."""

    def setUp(self):
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        from .serializers import GymTokenObtainPairSerializer

        self.api = APIClient()
        self.RefreshToken = RefreshToken
        self.GymTokenObtainPairSerializer = GymTokenObtainPairSerializer

        self.owner = self._make_user('owner.user', 'owner')
        self.trainer = self._make_user('trainer.user', 'trainer')
        self.member = self._make_user('member.user', 'client')
        self.other_member = self._make_user('other.user', 'client')

        self.member_client = self._make_client(
            user=self.member,
            name='Member Client',
            email='member.client@test.com',
            phone='+15550001',
        )
        self.other_client = self._make_client(
            user=self.other_member,
            name='Other Client',
            email='other.client@test.com',
            phone='+15550002',
        )

    def _make_user(self, username, role, password='pass1234'):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password=password,
        )
        profile = user.custom_profile
        profile.role = role
        profile.save()
        return user

    def _make_client(self, **kwargs):
        defaults = {
            'name': 'Client',
            'email': 'unique@test.com',
            'phone': '+15559999',
            'birth_date': date(1990, 1, 1),
            'weight': 70.0,
            'height': 175.0,
            'goals': [],
            'join_date': date.today(),
        }
        defaults.update(kwargs)
        return Client.objects.create(**defaults)

    def _auth(self, user):
        token = str(self.RefreshToken.for_user(user).access_token)
        self.api.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_clients_list_requires_authentication(self):
        response = self.api.get('/api/clients/')
        self.assertEqual(response.status_code, 401)

    def test_member_cannot_list_clients(self):
        self._auth(self.member)
        response = self.api.get('/api/clients/')
        self.assertEqual(response.status_code, 403)

    def test_member_can_read_own_profile_via_me(self):
        self._auth(self.member)
        response = self.api.get('/api/clients/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.member_client.id)
        self.assertIsNone(response.data.get('default_password'))

    def test_member_cannot_read_other_client(self):
        self._auth(self.member)
        response = self.api.get(f'/api/clients/{self.other_client.id}/')
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_delete_own_client(self):
        self._auth(self.member)
        response = self.api.delete(f'/api/clients/{self.member_client.id}/')
        self.assertEqual(response.status_code, 403)

    def test_member_can_read_catalog(self):
        self._auth(self.member)
        response = self.api.get('/api/exercises/')
        self.assertEqual(response.status_code, 200)

    def test_member_cannot_create_exercise(self):
        self._auth(self.member)
        response = self.api.post('/api/exercises/', {
            'name': 'Squat',
            'description': 'desc',
            'muscle_groups': ['legs'],
            'equipment': [],
            'difficulty': 'beginner',
            'instructions': [],
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_trainer_can_list_clients_but_cannot_delete_or_see_credentials(self):
        self._auth(self.trainer)
        list_response = self.api.get('/api/clients/')
        self.assertEqual(list_response.status_code, 200)

        delete_response = self.api.delete(f'/api/clients/{self.other_client.id}/')
        self.assertEqual(delete_response.status_code, 403)

        credentials = self.api.get(f'/api/clients/{self.other_client.id}/credentials/')
        self.assertEqual(credentials.status_code, 403)

        all_credentials = self.api.get('/api/clients/all_credentials/')
        self.assertEqual(all_credentials.status_code, 403)

    def test_owner_can_delete_client_and_see_credentials(self):
        self._auth(self.owner)
        credentials = self.api.get(f'/api/clients/{self.other_client.id}/credentials/')
        self.assertEqual(credentials.status_code, 200)
        self.assertIn('default_password', credentials.data)

        delete_response = self.api.delete(f'/api/clients/{self.other_client.id}/')
        self.assertIn(delete_response.status_code, (200, 204))

    def test_owner_sees_default_password_on_client(self):
        self._auth(self.owner)
        response = self.api.get(f'/api/clients/{self.member_client.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('default_password'))

    def test_jwt_contains_role_claim(self):
        token = self.GymTokenObtainPairSerializer.get_token(self.trainer)
        self.assertEqual(token['role'], 'trainer')
        self.assertEqual(token['user_id'], self.trainer.id)

    def test_assign_user_roles_preserves_staff(self):
        from django.core.management import call_command

        call_command('assign_user_roles')
        self.owner.custom_profile.refresh_from_db()
        self.trainer.custom_profile.refresh_from_db()
        self.assertEqual(self.owner.custom_profile.role, 'owner')
        self.assertEqual(self.trainer.custom_profile.role, 'trainer')

    def test_trainer_cannot_list_or_patch_users(self):
        self._auth(self.trainer)
        list_response = self.api.get('/api/users/')
        self.assertEqual(list_response.status_code, 403)

        patch_response = self.api.patch(
            f'/api/users/{self.member.id}/',
            {'role': 'trainer'},
            format='json',
        )
        self.assertEqual(patch_response.status_code, 403)

    def test_member_cannot_list_or_patch_users(self):
        self._auth(self.member)
        list_response = self.api.get('/api/users/')
        self.assertEqual(list_response.status_code, 403)

        patch_response = self.api.patch(
            f'/api/users/{self.trainer.id}/',
            {'role': 'client'},
            format='json',
        )
        self.assertEqual(patch_response.status_code, 403)

    def test_owner_can_list_users(self):
        self._auth(self.owner)
        response = self.api.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        usernames = {item['username'] for item in response.data['results']}
        self.assertIn(self.owner.username, usernames)
        self.assertIn(self.trainer.username, usernames)
        self.assertIn(self.member.username, usernames)

    def test_owner_can_filter_users_by_role(self):
        self._auth(self.owner)
        response = self.api.get('/api/users/', {'role': 'trainer'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['results'])
        self.assertTrue(all(item['role'] == 'trainer' for item in response.data['results']))

    def test_owner_can_change_client_to_trainer(self):
        self._auth(self.owner)
        response = self.api.patch(
            f'/api/users/{self.member.id}/',
            {'role': 'trainer'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['role'], 'trainer')
        self.member.custom_profile.refresh_from_db()
        self.assertEqual(self.member.custom_profile.role, 'trainer')
        self.assertEqual(response.data['client_id'], self.member_client.id)

    def test_cannot_demote_last_owner(self):
        self._auth(self.owner)
        response = self.api.patch(
            f'/api/users/{self.owner.id}/',
            {'role': 'trainer'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.owner.custom_profile.refresh_from_db()
        self.assertEqual(self.owner.custom_profile.role, 'owner')

    def test_owner_can_demote_when_another_owner_exists(self):
        second_owner = self._make_user('second.owner', 'owner')
        self._auth(self.owner)
        response = self.api.patch(
            f'/api/users/{second_owner.id}/',
            {'role': 'trainer'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['role'], 'trainer')
        second_owner.custom_profile.refresh_from_db()
        self.assertEqual(second_owner.custom_profile.role, 'trainer')

    def _make_exercise(self):
        return Exercise.objects.create(
            name='Squat',
            description='desc',
            muscle_groups=['legs'],
            equipment=[],
            difficulty='beginner',
            instructions=[],
        )

    def _image_file(self, name='exercise.png', content_type='image/png'):
        return SimpleUploadedFile(name, b'\x89PNG\r\n\x1a\n', content_type=content_type)

    def test_exercise_upload_image_requires_authentication(self):
        exercise = self._make_exercise()
        response = self.api.post(
            f'/api/exercises/{exercise.id}/upload_image/',
            {'image': self._image_file()},
            format='multipart',
        )
        self.assertEqual(response.status_code, 401)

    def test_member_cannot_upload_exercise_image(self):
        exercise = self._make_exercise()
        self._auth(self.member)
        response = self.api.post(
            f'/api/exercises/{exercise.id}/upload_image/',
            {'image': self._image_file()},
            format='multipart',
        )
        self.assertEqual(response.status_code, 403)

    @patch('gym.views.upload_file_to_s3', return_value='https://cdn.example.com/exercises/img.png')
    @patch('gym.views.delete_file_from_s3', return_value=True)
    def test_trainer_can_upload_exercise_image(self, _delete, _upload):
        exercise = self._make_exercise()
        self._auth(self.trainer)
        response = self.api.post(
            f'/api/exercises/{exercise.id}/upload_image/',
            {'image': self._image_file()},
            format='multipart',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['image_url'], 'https://cdn.example.com/exercises/img.png')
        exercise.refresh_from_db()
        self.assertEqual(exercise.image_url, 'https://cdn.example.com/exercises/img.png')

    def test_upload_exercise_image_requires_file(self):
        exercise = self._make_exercise()
        self._auth(self.trainer)
        response = self.api.post(
            f'/api/exercises/{exercise.id}/upload_image/',
            {},
            format='multipart',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_upload_exercise_image_rejects_invalid_type(self):
        exercise = self._make_exercise()
        self._auth(self.trainer)
        response = self.api.post(
            f'/api/exercises/{exercise.id}/upload_image/',
            {'image': self._image_file(name='notes.txt', content_type='text/plain')},
            format='multipart',
        )
        self.assertEqual(response.status_code, 400)
        exercise.refresh_from_db()
        self.assertIsNone(exercise.image_url)


class PlanCatalogTest(TestCase):
    """CRUD de planes: 401, 403 por rol, reglas de negocio y filtros."""

    def setUp(self):
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        self.api = APIClient()
        self.RefreshToken = RefreshToken
        self.owner = self._make_user('owner.user', 'owner')
        self.trainer = self._make_user('trainer.user', 'trainer')
        self.member = self._make_user('member.user', 'client')
        self.plan_payload = {
            'name': 'Gold',
            'slug': 'gold',
            'description': 'Plan de prueba',
            'price': 150000,
            'duration_days': 30,
            'features': ['Acceso completo'],
            'color': 'orange',
            'is_active': True,
        }

    def _make_user(self, username, role, password='pass1234'):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password=password,
        )
        profile = user.custom_profile
        profile.role = role
        profile.save()
        return user

    def _make_client(self, **kwargs):
        defaults = {
            'name': 'Client',
            'email': 'unique-plan@test.com',
            'phone': '+15558888',
            'birth_date': date(1990, 1, 1),
            'weight': 70.0,
            'height': 175.0,
            'goals': [],
            'join_date': date.today(),
        }
        defaults.update(kwargs)
        return Client.objects.create(**defaults)

    def _auth(self, user):
        token = str(self.RefreshToken.for_user(user).access_token)
        self.api.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_plans_list_requires_authentication(self):
        response = self.api.get('/api/plans/')
        self.assertEqual(response.status_code, 401)

    def test_member_cannot_list_or_create_plans(self):
        self._auth(self.member)
        list_response = self.api.get('/api/plans/')
        self.assertEqual(list_response.status_code, 403)

        create_response = self.api.post('/api/plans/', self.plan_payload, format='json')
        self.assertEqual(create_response.status_code, 403)

    def test_trainer_can_list_but_cannot_write(self):
        self._auth(self.trainer)
        list_response = self.api.get('/api/plans/')
        self.assertEqual(list_response.status_code, 200)
        self.assertGreaterEqual(list_response.data['count'], 3)

        create_response = self.api.post('/api/plans/', self.plan_payload, format='json')
        self.assertEqual(create_response.status_code, 403)

        seeded = Plan.objects.get(slug='standard')
        patch_response = self.api.patch(
            f'/api/plans/{seeded.id}/',
            {'price': 1},
            format='json',
        )
        self.assertEqual(patch_response.status_code, 403)

        delete_response = self.api.delete(f'/api/plans/{seeded.id}/')
        self.assertEqual(delete_response.status_code, 403)

    def test_owner_can_create_update_and_filter(self):
        self._auth(self.owner)
        create_response = self.api.post('/api/plans/', self.plan_payload, format='json')
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data['slug'], 'gold')
        plan_id = create_response.data['id']

        patch_response = self.api.patch(
            f'/api/plans/{plan_id}/',
            {'price': 180000},
            format='json',
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.data['price'], 180000)

        search_response = self.api.get('/api/plans/', {'search': 'gold'})
        self.assertEqual(search_response.status_code, 200)
        slugs = {item['slug'] for item in search_response.data['results']}
        self.assertEqual(slugs, {'gold'})

        active_response = self.api.get('/api/plans/', {'is_active': True})
        self.assertEqual(active_response.status_code, 200)
        self.assertTrue(all(item['is_active'] for item in active_response.data['results']))

    def test_cannot_delete_plan_with_clients(self):
        self._auth(self.owner)
        standard = Plan.objects.get(slug='standard')
        self._make_client(subscription_type='standard')

        response = self.api.delete(f'/api/plans/{standard.id}/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Plan.objects.filter(pk=standard.pk).exists())

    def test_cannot_delete_last_plan(self):
        self._auth(self.owner)
        Plan.objects.exclude(slug='standard').delete()
        last_plan = Plan.objects.get(slug='standard')

        response = self.api.delete(f'/api/plans/{last_plan.id}/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Plan.objects.filter(pk=last_plan.pk).exists())

    def test_cannot_deactivate_last_active_plan(self):
        self._auth(self.owner)
        Plan.objects.exclude(slug='standard').update(is_active=False)
        last_active = Plan.objects.get(slug='standard')

        response = self.api.patch(
            f'/api/plans/{last_active.id}/',
            {'is_active': False},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        last_active.refresh_from_db()
        self.assertTrue(last_active.is_active)

    def test_client_rejects_unknown_plan_slug(self):
        self._auth(self.owner)
        response = self.api.post('/api/clients/', {
            'name': 'Nuevo',
            'email': 'nuevo.plan@test.com',
            'phone': '+15557777',
            'birth_date': '1990-01-01',
            'weight': 70,
            'height': 175,
            'goals': ['Fuerza'],
            'join_date': str(date.today()),
            'subscription_type': 'no-existe',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Client.objects.filter(email='nuevo.plan@test.com').exists())

    def test_client_includes_nested_plan(self):
        self._auth(self.owner)
        client = self._make_client(subscription_type='premium')
        response = self.api.get(f'/api/clients/{client.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['subscription_type'], 'premium')
        self.assertEqual(response.data['plan']['slug'], 'premium')
        self.assertEqual(response.data['plan']['name'], 'Premium')


class CompleteWorkoutTest(RoleBasedAccessTest):
    """MVP: registrar inicio/fin de un entrenamiento con complete_workout."""

    def setUp(self):
        super().setUp()
        from .models import ClientRoutine, Routine, Workout

        self.workout = Workout.objects.create(
            name='Fuerza piernas',
            description='Sentadillas y peso muerto',
            estimated_duration=40,
            difficulty='beginner',
            category='strength',
        )
        self.other_workout = Workout.objects.create(
            name='Cardio',
            description='Cinta',
            estimated_duration=20,
            difficulty='beginner',
            category='cardio',
        )
        self.routine = Routine.objects.create(
            name='Rutina test',
            description='Desc',
            frequency='weekly',
            days_per_week=3,
            duration=4,
        )
        self.routine.workouts.add(self.workout)
        self.assignment = ClientRoutine.objects.create(
            client=self.member_client,
            routine=self.routine,
            start_date=date.today(),
            is_active=True,
            assigned_days=['friday'],
        )
        self.other_assignment = ClientRoutine.objects.create(
            client=self.other_client,
            routine=self.routine,
            start_date=date.today(),
            is_active=True,
            assigned_days=['friday'],
        )
        self.url = f'/api/client-routines/{self.assignment.id}/complete_workout/'

    def test_complete_workout_requires_authentication(self):
        response = self.api.post(self.url, {'workout_id': self.workout.id}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_member_cannot_complete_other_client_workout(self):
        self._auth(self.member)
        response = self.api.post(
            f'/api/client-routines/{self.other_assignment.id}/complete_workout/',
            {'workout_id': self.workout.id},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_member_can_complete_own_workout_with_started_at(self):
        self._auth(self.member)
        started = timezone.now() - timedelta(minutes=25)
        response = self.api.post(self.url, {
            'workout_id': self.workout.id,
            'started_at': started.isoformat(),
            'notes': 'Sesión de prueba',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['workout']['id'], self.workout.id)
        self.assertIsNotNone(response.data['completed_at'])
        self.assertIsNotNone(response.data['started_at'])
        self.assertEqual(response.data['notes'], 'Sesión de prueba')

    def test_complete_workout_requires_workout_id(self):
        self._auth(self.member)
        response = self.api.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)

    def test_complete_workout_rejects_workout_outside_routine(self):
        self._auth(self.member)
        response = self.api.post(self.url, {'workout_id': self.other_workout.id}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_member_can_read_own_progress(self):
        self._auth(self.member)
        self.api.post(self.url, {'workout_id': self.workout.id}, format='json')
        response = self.api.get(f'/api/client-routines/{self.assignment.id}/progress/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_trainer_can_complete_client_workout(self):
        self._auth(self.trainer)
        response = self.api.post(self.url, {'workout_id': self.workout.id}, format='json')
        self.assertEqual(response.status_code, 201)


class ImageOptimizationTest(TestCase):
    """Pillow reduce dimensiones y convierte a JPEG antes de S3."""

    def _png(self, width, height, name='photo.png'):
        from io import BytesIO
        from PIL import Image

        buffer = BytesIO()
        Image.new('RGB', (width, height), color='red').save(buffer, format='PNG')
        return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')

    def test_resizes_large_exercise_image(self):
        from PIL import Image
        from gym.services.image_utils import optimize_image

        original = self._png(3000, 2000)
        optimized = optimize_image(original, folder='exercises')
        image = Image.open(optimized)

        self.assertEqual(optimized.content_type, 'image/jpeg')
        self.assertTrue(optimized.name.endswith('.jpg'))
        self.assertLessEqual(max(image.size), 1600)
        self.assertLess(optimized.size, original.size)

    def test_profile_images_use_smaller_max(self):
        from PIL import Image
        from gym.services.image_utils import optimize_image

        optimized = optimize_image(self._png(2000, 2000), folder='profiles')
        image = Image.open(optimized)
        self.assertLessEqual(max(image.size), 800)

    def test_small_image_keeps_size(self):
        from PIL import Image
        from gym.services.image_utils import optimize_image

        optimized = optimize_image(self._png(400, 300), folder='exercises')
        image = Image.open(optimized)
        self.assertEqual(image.size, (400, 300))
        self.assertEqual(optimized.content_type, 'image/jpeg')
