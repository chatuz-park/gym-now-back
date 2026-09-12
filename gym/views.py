from datetime import timedelta
from django.shortcuts import render
from django.db import models
from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Prefetch, Q
from django.db.models.functions import TruncDate
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets, status, filters, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .filters import ClientFilter, RoutineFilter, ExerciseFilter, WorkoutFilter, GoalFilter, UserFilter, PlanFilter
from .models import (
    Client, Exercise, Workout, WorkoutSet, Routine,
    ClientRoutine, RoutineProgress, ProgressMetrics, Goal, Plan
)
from .serializers import (
    ClientSerializer, ExerciseSerializer, WorkoutSerializer, WorkoutSetSerializer,
    RoutineSerializer, ClientRoutineSerializer, ClientRoutineListSerializer,
    RoutineProgressSerializer, RoutineProgressListSerializer,
    ProgressMetricsSerializer, GoalSerializer, WorkoutCreateSerializer, RoutineCreateSerializer,
    UserProfileSerializer, UserRoleAdminSerializer, ProfileImageUploadSerializer,
    ExerciseImageUploadSerializer, GymTokenObtainPairSerializer,
    PlanSerializer,
)
from .services import upload_file_to_s3, delete_file_from_s3
from .permissions import (
    RoleMapMixin, ALL_ROLES, STAFF_ROLES, OWNER_ROLES,
    get_user_role, get_user_client, is_member_role, is_staff_role,
)

ROUTINE_TREE_PREFETCH = (
    'routine__workouts__sets__exercise',
)

ACTIVE_CLIENT_ROUTINES = Prefetch(
    'client_routines',
    queryset=ClientRoutine.objects.filter(is_active=True)
        .select_related('routine')
        .prefetch_related(*ROUTINE_TREE_PREFETCH),
)

# Create your views here.

class PlanViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PlanFilter
    ordering_fields = ['name', 'price', 'duration_days']
    ordering = ['price', 'name']
    role_map = {
        'list': STAFF_ROLES,
        'retrieve': STAFF_ROLES,
        'create': OWNER_ROLES,
        'update': OWNER_ROLES,
        'partial_update': OWNER_ROLES,
        'destroy': OWNER_ROLES,
        'default': OWNER_ROLES,
    }

    @swagger_auto_schema(
        operation_description="Lista de planes de suscripción",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'name', '-price'",
                type=openapi.TYPE_STRING,
                enum=['name', '-name', 'price', '-price', 'duration_days', '-duration_days'],
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Búsqueda en nombre, código y descripción",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'is_active',
                openapi.IN_QUERY,
                description="Filtrar por planes activos",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_destroy(self, instance):
        from rest_framework.exceptions import ValidationError

        if Client.objects.filter(subscription_type=instance.slug).exists():
            raise ValidationError({
                'detail': 'No se puede eliminar un plan con clientes asignados. Desactívalo.',
            })
        if Plan.objects.count() <= 1:
            raise ValidationError({
                'detail': 'No se puede eliminar el último plan.',
            })
        instance.delete()


class ClientViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ClientFilter
    ordering_fields = ['name', 'join_date', 'birth_date', 'weight', 'height']
    ordering = ['-join_date']  # Más reciente primero
    role_map = {
        'list': STAFF_ROLES,
        'create': STAFF_ROLES,
        'retrieve': ALL_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': OWNER_ROLES,
        'progress': ALL_ROLES,
        'goals': ALL_ROLES,
        'routines': ALL_ROLES,
        'credentials': OWNER_ROLES,
        'all_credentials': OWNER_ROLES,
        'statistics': STAFF_ROLES,
        'me': ALL_ROLES,
        'upload_profile_image': ALL_ROLES,
    }
    object_permission_actions = frozenset({
        'retrieve', 'progress', 'goals', 'routines', 'upload_profile_image',
    })

    def get_queryset(self):
        queryset = Client.objects.select_related('user')
        if self.action in ('list', 'retrieve', 'me', 'routines'):
            queryset = queryset.prefetch_related(ACTIVE_CLIENT_ROUTINES)
        return queryset

    @swagger_auto_schema(
        operation_description="Lista de clientes con ordenamiento configurable",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'name', '-join_date', 'weight'",
                type=openapi.TYPE_STRING,
                enum=['name', '-name', 'join_date', '-join_date', 'birth_date', '-birth_date', 'weight', '-weight', 'height', '-height']
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Búsqueda en nombre, email, teléfono y contacto de emergencia",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Obtener el progreso de un cliente específico"""
        client = self.get_object()
        progress = ProgressMetrics.objects.filter(client=client).select_related('client').order_by('-date')
        serializer = ProgressMetricsSerializer(progress, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def goals(self, request, pk=None):
        """Obtener los objetivos de un cliente específico"""
        client = self.get_object()
        goals = Goal.objects.filter(client=client).select_related('client')
        serializer = GoalSerializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def routines(self, request, pk=None):
        """Obtener las rutinas asignadas a un cliente, incluyendo días asignados y detalles de la asignación"""
        client = self.get_object()
        from .serializers import ClientRoutineDetailSerializer
        assignments = client.client_routines.filter(is_active=True).select_related('routine').prefetch_related(
            *ROUTINE_TREE_PREFETCH
        )
        serializer = ClientRoutineDetailSerializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def credentials(self, request, pk=None):
        """Obtener las credenciales de acceso de un cliente"""
        client = self.get_object()
        if not client.user:
            return Response(
                {'error': 'No se encontró usuario asociado a este cliente'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'username': client.user.username,
            'email': client.user.email,
            'default_password': client.generate_default_password(),
            'client_name': client.name,
            'age': client.age,
            'birth_date': client.birth_date
        })

    @action(detail=False, methods=['get'])
    def all_credentials(self, request):
        """Obtener las credenciales de acceso de todos los clientes"""
        clients = self.get_queryset().filter(user__isnull=False)
        credentials_list = []
        
        for client in clients:
            credentials_list.append({
                'client_id': client.id,
                'client_name': client.name,
                'username': client.user.username,
                'email': client.user.email,
                'default_password': client.generate_default_password(),
                'age': client.age,
                'birth_date': client.birth_date
            })
        
        return Response(credentials_list)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtener estadísticas de los clientes"""
        from django.db.models import Avg, Count, Min, Max
        from django.utils import timezone
        
        total_clients = Client.objects.count()
        active_subscriptions = Client.objects.filter(
            models.Q(subscription_end__isnull=True) | 
            models.Q(subscription_end__gt=timezone.now().date())
        ).count()
        
        subscription_stats = Client.objects.values('subscription_type').annotate(
            count=Count('id')
        )
        
        # Estadísticas de edad
        age_stats = Client.objects.aggregate(
            avg_age=Avg('age'),
            min_age=Min('age'),
            max_age=Max('age')
        )
        
        # Estadísticas de peso
        weight_stats = Client.objects.aggregate(
            avg_weight=Avg('weight'),
            min_weight=Min('weight'),
            max_weight=Max('weight')
        )
        
        # Clientes por mes de registro
        monthly_registrations = Client.objects.extra(
            select={'month': "EXTRACT(month FROM join_date)"}
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        return Response({
            'total_clients': total_clients,
            'active_subscriptions': active_subscriptions,
            'subscription_stats': subscription_stats,
            'age_stats': age_stats,
            'weight_stats': weight_stats,
            'monthly_registrations': monthly_registrations
        })

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtener los datos del cliente autenticado"""
        client = get_user_client(request.user)
        if client is None:
            return Response(
                {'error': 'No se encontró perfil de cliente para este usuario'},
                status=status.HTTP_404_NOT_FOUND
            )
        client = self.get_queryset().filter(pk=client.pk).first() or client
        serializer = self.get_serializer(client)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='post',
        operation_description="Subir imagen de perfil del cliente a S3. El ID del cliente va en la URL.",
        request_body=ProfileImageUploadSerializer,
        responses={
            200: openapi.Response(
                description="Imagen subida exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'profile_image': openapi.Schema(type=openapi.TYPE_STRING, description='URL de la imagen'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Mensaje de confirmación')
                    }
                )
            ),
            400: "Error en la solicitud",
            404: "Cliente no encontrado"
        }
    )
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_profile_image(self, request, pk=None):
        """Subir imagen de perfil del cliente a S3"""
        client = self.get_object()
        
        if 'profile_image' not in request.FILES:
            return Response(
                {'error': 'Se requiere el archivo profile_image'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['profile_image']
        
        # Validar tipo de archivo
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            return Response(
                {'error': 'Tipo de archivo no permitido. Use JPG, PNG, GIF o WebP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Eliminar imagen anterior si existe
        if client.profile_image:
            delete_file_from_s3(client.profile_image)
        
        # Subir nueva imagen
        file_url = upload_file_to_s3(file, folder="profiles")
        
        if not file_url:
            return Response(
                {'error': 'Error al subir la imagen'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Actualizar cliente
        client.profile_image = file_url
        client.save(update_fields=['profile_image'])
        
        return Response({
            'profile_image': file_url,
            'message': 'Imagen de perfil actualizada exitosamente'
        })

class ExerciseViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ExerciseFilter
    ordering_fields = ['name', 'difficulty']
    ordering = ['name']
    role_map = {
        'list': ALL_ROLES,
        'retrieve': ALL_ROLES,
        'create': STAFF_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': STAFF_ROLES,
        'by_difficulty': ALL_ROLES,
        'by_muscle_group': ALL_ROLES,
        'upload_image': STAFF_ROLES,
    }

    @swagger_auto_schema(
        operation_description="Lista de ejercicios con ordenamiento configurable",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'name', '-difficulty'",
                type=openapi.TYPE_STRING,
                enum=['name', '-name', 'difficulty', '-difficulty']
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Búsqueda en nombre y descripción",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def by_difficulty(self, request):
        """Obtener ejercicios por nivel de dificultad"""
        difficulty = request.query_params.get('difficulty', 'beginner')
        exercises = self.queryset.filter(difficulty=difficulty)
        serializer = self.get_serializer(exercises, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_muscle_group(self, request):
        """Obtener ejercicios por grupo muscular"""
        muscle_group = request.query_params.get('muscle_group', '')
        exercises = self.queryset.filter(muscle_groups__contains=[muscle_group])
        serializer = self.get_serializer(exercises, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='post',
        operation_description="Subir imagen del ejercicio a S3. El ID del ejercicio va en la URL.",
        request_body=ExerciseImageUploadSerializer,
        responses={
            200: openapi.Response(
                description="Imagen subida exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'image_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL de la imagen'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Mensaje de confirmación')
                    }
                )
            ),
            400: "Error en la solicitud",
            404: "Ejercicio no encontrado"
        }
    )
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        """Subir imagen del ejercicio a S3"""
        exercise = self.get_object()

        if 'image' not in request.FILES:
            return Response(
                {'error': 'Se requiere el archivo image'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['image']

        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            return Response(
                {'error': 'Tipo de archivo no permitido. Use JPG, PNG, GIF o WebP'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if exercise.image_url:
            delete_file_from_s3(exercise.image_url)

        file_url = upload_file_to_s3(file, folder="exercises")

        if not file_url:
            return Response(
                {'error': 'Error al subir la imagen'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        exercise.image_url = file_url
        exercise.save(update_fields=['image_url'])

        return Response({
            'image_url': file_url,
            'message': 'Imagen del ejercicio actualizada exitosamente'
        })

class WorkoutViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = Workout.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = WorkoutFilter
    ordering_fields = ['name', 'difficulty', 'estimated_duration']
    ordering = ['name']
    role_map = {
        'list': ALL_ROLES,
        'retrieve': ALL_ROLES,
        'create': STAFF_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': STAFF_ROLES,
        'sets': ALL_ROLES,
        'by_category': ALL_ROLES,
    }

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WorkoutCreateSerializer
        return WorkoutSerializer

    @swagger_auto_schema(
        operation_description="Lista de workouts con ordenamiento configurable",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'name', '-difficulty', 'estimated_duration'",
                type=openapi.TYPE_STRING,
                enum=['name', '-name', 'difficulty', '-difficulty', 'estimated_duration', '-estimated_duration']
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Búsqueda en nombre y descripción",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def sets(self, request, pk=None):
        """Obtener los sets de un workout específico"""
        workout = self.get_object()
        sets = workout.sets.all()
        serializer = WorkoutSetSerializer(sets, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Obtener workouts por categoría"""
        category = request.query_params.get('category', 'strength')
        workouts = self.queryset.filter(category=category)
        serializer = self.get_serializer(workouts, many=True)
        return Response(serializer.data)

class WorkoutSetViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = WorkoutSet.objects.all()
    serializer_class = WorkoutSetSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['workout', 'exercise', 'completed']
    ordering_fields = ['reps', 'weight', 'rest_time']
    ordering = ['-id']  # Más reciente primero
    role_map = {
        'list': ALL_ROLES,
        'retrieve': ALL_ROLES,
        'create': STAFF_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': STAFF_ROLES,
    }

    @swagger_auto_schema(
        operation_description="Lista de workout sets con ordenamiento configurable",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'reps', '-weight', 'rest_time'",
                type=openapi.TYPE_STRING,
                enum=['reps', '-reps', 'weight', '-weight', 'rest_time', '-rest_time']
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class RoutineViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = Routine.objects.all()
    serializer_class = RoutineSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RoutineFilter
    ordering_fields = ['name', 'duration', 'days_per_week', 'frequency']
    ordering = ['name']
    role_map = {
        'list': ALL_ROLES,
        'retrieve': ALL_ROLES,
        'create': STAFF_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': STAFF_ROLES,
        'workouts': ALL_ROLES,
        'by_frequency': ALL_ROLES,
        'statistics': STAFF_ROLES,
    }

    @swagger_auto_schema(
        operation_description="Lista de rutinas con ordenamiento configurable",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'name', '-duration', 'days_per_week'",
                type=openapi.TYPE_STRING,
                enum=['name', '-name', 'duration', '-duration', 'days_per_week', '-days_per_week', 'frequency', '-frequency']
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Búsqueda en nombre y descripción",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RoutineCreateSerializer
        return RoutineSerializer

    @action(detail=True, methods=['get'])
    def workouts(self, request, pk=None):
        """Obtener los workouts de una rutina específica"""
        routine = self.get_object()
        workouts = routine.workouts.all()
        serializer = WorkoutSerializer(workouts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_frequency(self, request):
        """Obtener rutinas por frecuencia"""
        frequency = request.query_params.get('frequency', 'weekly')
        routines = self.queryset.filter(frequency=frequency)
        serializer = self.get_serializer(routines, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtener estadísticas de las rutinas"""
        from django.db.models import Avg, Count, Min, Max
        
        total_routines = Routine.objects.count()
        
        # Estadísticas por frecuencia
        frequency_stats = Routine.objects.values('frequency').annotate(
            count=Count('id')
        )
        
        # Estadísticas de duración
        duration_stats = Routine.objects.aggregate(
            avg_duration=Avg('duration'),
            min_duration=Min('duration'),
            max_duration=Max('duration')
        )
        
        # Estadísticas de días por semana
        days_stats = Routine.objects.aggregate(
            avg_days=Avg('days_per_week'),
            min_days=Min('days_per_week'),
            max_days=Max('days_per_week')
        )
        
        # Rutinas por número de workouts
        workout_count_stats = Routine.objects.annotate(
            workout_count=Count('workouts')
        ).values('workout_count').annotate(
            routine_count=Count('id')
        ).order_by('workout_count')
        
        # Rutinas más populares (con más clientes asignados)
        popular_routines = Routine.objects.annotate(
            client_count=Count('client_routines')
        ).order_by('-client_count')[:10]
        
        popular_routines_data = []
        for routine in popular_routines:
            popular_routines_data.append({
                'id': routine.id,
                'name': routine.name,
                'client_count': routine.client_count,
                'frequency': routine.frequency,
                'duration': routine.duration
            })
        
        return Response({
            'total_routines': total_routines,
            'frequency_stats': frequency_stats,
            'duration_stats': duration_stats,
            'days_stats': days_stats,
            'workout_count_stats': workout_count_stats,
            'popular_routines': popular_routines_data
        })

class ClientRoutineViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = ClientRoutine.objects.all()
    serializer_class = ClientRoutineSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'routine', 'is_active', 'start_date']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']
    role_map = {
        'list': ALL_ROLES,
        'create': STAFF_ROLES,
        'retrieve': ALL_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': STAFF_ROLES,
        'progress': ALL_ROLES,
        'complete_workout': ALL_ROLES,
    }
    object_permission_actions = frozenset({
        'retrieve', 'progress', 'complete_workout',
    })

    def get_serializer_class(self):
        if self.action == 'list':
            return ClientRoutineListSerializer
        return ClientRoutineSerializer

    def get_queryset(self):
        queryset = ClientRoutine.objects.select_related('client', 'client__user', 'routine')
        if self.action != 'list':
            queryset = queryset.prefetch_related(*ROUTINE_TREE_PREFETCH)
        if self.action == 'list' and is_member_role(get_user_role(self.request.user)):
            client = get_user_client(self.request.user)
            if client is None:
                return queryset.none()
            return queryset.filter(client=client)
        return queryset

    @swagger_auto_schema(
        operation_description="Lista de rutinas de clientes con ordenamiento configurable",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'start_date', '-end_date'",
                type=openapi.TYPE_STRING,
                enum=['start_date', '-start_date', 'end_date', '-end_date']
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Actualizar una rutina de cliente. Para assigned_days, puedes enviar:\n"
                            "1. Lista de días: ['monday', 'wednesday', 'friday']\n"
                            "2. Objeto con valores booleanos: {'monday': true, 'wednesday': true, 'friday': true}\n"
                            "Días válidos: monday, tuesday, wednesday, thursday, friday, saturday, sunday",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'client_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del cliente'),
                'routine_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID de la rutina'),
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Fecha de inicio'),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Fecha de fin (opcional)'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Si la rutina está activa'),
                'assigned_days': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Días asignados. Puede ser objeto con valores booleanos o lista de días',
                    properties={
                        'monday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'tuesday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'wednesday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'thursday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'friday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'saturday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'sunday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            }
        )
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Actualizar parcialmente una rutina de cliente. Para assigned_days, puedes enviar:\n"
                            "1. Lista de días: ['monday', 'wednesday', 'friday']\n"
                            "2. Objeto con valores booleanos: {'monday': true, 'wednesday': true, 'friday': true}\n"
                            "Días válidos: monday, tuesday, wednesday, thursday, friday, saturday, sunday",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'client_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del cliente'),
                'routine_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID de la rutina'),
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Fecha de inicio'),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Fecha de fin (opcional)'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Si la rutina está activa'),
                'assigned_days': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Días asignados. Puede ser objeto con valores booleanos o lista de días',
                    properties={
                        'monday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'tuesday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'wednesday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'thursday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'friday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'saturday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'sunday': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            }
        )
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Obtener el progreso de una rutina de cliente específica"""
        client_routine = self.get_object()
        progress = (
            RoutineProgress.objects.filter(client_routine=client_routine)
            .select_related('client_routine__client', 'workout')
            .order_by('-completed_at')
        )
        serializer = RoutineProgressSerializer(progress, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description=(
            "Registrar una sesión de entrenamiento. Marca completed_at al momento del POST. "
            "started_at es opcional (hora en que el socio pulsó Iniciar)."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['workout_id'],
            properties={
                'workout_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del entrenamiento'),
                'started_at': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='date-time',
                    description='Hora de inicio de la sesión (ISO 8601)',
                ),
                'notes': openapi.Schema(type=openapi.TYPE_STRING, description='Notas opcionales'),
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description='Valoración opcional'),
            },
        ),
        responses={201: RoutineProgressSerializer()},
    )
    @action(detail=True, methods=['post'])
    def complete_workout(self, request, pk=None):
        """Registrar el fin de un workout y, si viene, la hora de inicio."""
        client_routine = self.get_object()
        workout_id = request.data.get('workout_id')
        notes = request.data.get('notes', '') or ''
        rating = request.data.get('rating', None)
        started_at_raw = request.data.get('started_at')

        if not workout_id:
            return Response(
                {'detail': 'workout_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            workout = Workout.objects.get(id=workout_id)
        except Workout.DoesNotExist:
            return Response(
                {'error': 'Workout no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not client_routine.routine.workouts.filter(id=workout.id).exists():
            return Response(
                {'detail': 'Este entrenamiento no pertenece a la rutina asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        started_at = None
        if started_at_raw:
            started_at = parse_datetime(str(started_at_raw))
            if started_at is None:
                return Response(
                    {'detail': 'started_at no es una fecha válida'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if timezone.is_naive(started_at):
                started_at = timezone.make_aware(started_at)
            if started_at > timezone.now():
                return Response(
                    {'detail': 'started_at no puede ser futuro'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        completed_at = timezone.now()
        if started_at and started_at > completed_at:
            return Response(
                {'detail': 'started_at no puede ser posterior a la hora de fin'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        progress = RoutineProgress.objects.create(
            client_routine=client_routine,
            workout=workout,
            started_at=started_at,
            completed_at=completed_at,
            notes=notes,
            rating=rating,
        )
        serializer = RoutineProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class RoutineProgressViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = RoutineProgress.objects.all()
    serializer_class = RoutineProgressSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return RoutineProgressListSerializer
        return RoutineProgressSerializer

    def get_queryset(self):
        queryset = RoutineProgress.objects.select_related(
            'client_routine__client',
            'client_routine__routine',
            'workout',
        )
        if self.action != 'list':
            queryset = queryset.prefetch_related(
                *ROUTINE_TREE_PREFETCH,
                'workout__sets__exercise',
            )
        return queryset
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client_routine', 'workout', 'completed_at']
    ordering_fields = ['completed_at', 'rating']
    ordering = ['-completed_at']
    role_map = {
        'list': STAFF_ROLES,
        'create': STAFF_ROLES,
        'retrieve': ALL_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': STAFF_ROLES,
    }
    object_permission_actions = frozenset({'retrieve'})

    @swagger_auto_schema(
        operation_description="Lista de progreso de rutinas con ordenamiento configurable",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'completed_at', '-rating'",
                type=openapi.TYPE_STRING,
                enum=['completed_at', '-completed_at', 'rating', '-rating']
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class ProgressMetricsViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = ProgressMetrics.objects.all()
    serializer_class = ProgressMetricsSerializer

    def get_queryset(self):
        return ProgressMetrics.objects.select_related('client')
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'date']
    ordering_fields = ['date', 'weight', 'body_fat', 'muscle_mass']
    ordering = ['-date']
    role_map = {
        'list': STAFF_ROLES,
        'create': STAFF_ROLES,
        'retrieve': ALL_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': STAFF_ROLES,
        'client_progress': ALL_ROLES,
    }
    object_permission_actions = frozenset({'retrieve'})

    @swagger_auto_schema(
        operation_description="Lista de métricas de progreso con ordenamiento configurable",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'date', '-weight', 'body_fat'",
                type=openapi.TYPE_STRING,
                enum=['date', '-date', 'weight', '-weight', 'body_fat', '-body_fat', 'muscle_mass', '-muscle_mass']
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def client_progress(self, request):
        """Obtener el progreso de un cliente específico"""
        client_id = request.query_params.get('client_id')
        if not client_id:
            return Response(
                {'error': 'client_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if is_member_role(get_user_role(request.user)):
            own_client = get_user_client(request.user)
            if own_client is None or str(own_client.id) != str(client_id):
                return Response(
                    {'detail': 'No tienes permiso para acceder a este recurso.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        progress = self.get_queryset().filter(client_id=client_id).order_by('-date')
        serializer = self.get_serializer(progress, many=True)
        return Response(serializer.data)

class GoalViewSet(RoleMapMixin, viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer

    def get_queryset(self):
        return Goal.objects.select_related('client')
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = GoalFilter
    ordering_fields = ['deadline', 'target_value', 'current_value']
    ordering = ['deadline']  # Más urgente primero (deadline ascendente)
    role_map = {
        'list': STAFF_ROLES,
        'create': STAFF_ROLES,
        'retrieve': ALL_ROLES,
        'update': STAFF_ROLES,
        'partial_update': STAFF_ROLES,
        'destroy': STAFF_ROLES,
        'update_progress': ALL_ROLES,
        'completed': STAFF_ROLES,
        'pending': STAFF_ROLES,
    }
    object_permission_actions = frozenset({'retrieve', 'update_progress'})

    @swagger_auto_schema(
        operation_description="Lista de objetivos con ordenamiento configurable",
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para orden descendente. Ejemplos: 'deadline', '-target_value', 'current_value'",
                type=openapi.TYPE_STRING,
                enum=['deadline', '-deadline', 'target_value', '-target_value', 'current_value', '-current_value']
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Búsqueda en título y descripción",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Actualizar el progreso de un objetivo"""
        goal = self.get_object()
        current_value = request.data.get('current_value')
        
        if current_value is None:
            return Response(
                {'error': 'current_value es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.current_value = current_value
        goal.is_completed = current_value >= goal.target_value
        goal.save()
        
        serializer = self.get_serializer(goal)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Obtener objetivos completados"""
        goals = self.get_queryset().filter(is_completed=True)
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Obtener objetivos pendientes"""
        goals = self.get_queryset().filter(is_completed=False)
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def client_login(request):
    """Endpoint para que los clientes inicien sesión con sus credenciales"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Se requiere username y password'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Intentar autenticar al usuario
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response(
            {'error': 'Credenciales inválidas'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    client = get_user_client(user)
    if client is None:
        return Response(
            {'error': 'Usuario no tiene perfil de cliente'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    refresh = GymTokenObtainPairSerializer.get_token(user)
    
    return Response({
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        },
        'client': {
            'id': client.id,
            'name': client.name,
            'age': client.age,
            'birth_date': client.birth_date,
            'subscription_type': client.subscription_type
        }
    })

class UserViewSet(
    RoleMapMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Listado y asignación de roles. Solo owner; no crea ni borra cuentas."""
    queryset = User.objects.select_related('custom_profile', 'client_profile').all()
    serializer_class = UserRoleAdminSerializer
    http_method_names = ['get', 'patch', 'head', 'options']
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = UserFilter
    ordering_fields = ['username', 'date_joined']
    ordering = ['username']
    role_map = {
        'list': OWNER_ROLES,
        'retrieve': OWNER_ROLES,
        'partial_update': OWNER_ROLES,
        'default': OWNER_ROLES,
    }

    @swagger_auto_schema(
        operation_description="Lista usuarios con su rol. Solo owner.",
        operation_summary="Listar usuarios",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Búsqueda en username, email, nombre y apellido",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'role',
                openapi.IN_QUERY,
                description="Filtrar por rol",
                type=openapi.TYPE_STRING,
                enum=['client', 'guest', 'trainer', 'owner'],
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Campo de ordenamiento. Usar '-' para descendente.",
                type=openapi.TYPE_STRING,
                enum=['username', '-username', 'date_joined', '-date_joined'],
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Número de página",
                type=openapi.TYPE_INTEGER,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Cambia el rol de un usuario. No permite quitar el último owner.",
        operation_summary="Actualizar rol de usuario",
        request_body=UserRoleAdminSerializer,
        responses={200: UserRoleAdminSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


@swagger_auto_schema(
    method='get',
    responses={
        200: UserProfileSerializer,
        401: 'Unauthorized',
        500: 'Internal Server Error'
    },
    operation_description="Obtiene la información del usuario autenticado basado en el token de sesión JWT",
    operation_summary="Obtener información del usuario autenticado"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Endpoint para obtener la información del usuario autenticado basado en el token de sesión"""
    try:
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Error al obtener información del usuario: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


user_profile.cls.required_roles = ALL_ROLES
client_login.cls.required_roles = None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """KPIs del owner y series ligeras para las gráficas del inicio."""
    if not is_staff_role(get_user_role(request.user)):
        return Response(
            {'detail': 'No tienes permiso para acceder a este recurso.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    today = timezone.now().date()
    in_7 = today + timedelta(days=7)
    in_30 = today + timedelta(days=30)
    ago_7 = today - timedelta(days=7)
    ago_14 = today - timedelta(days=13)
    ago_30 = today - timedelta(days=30)
    week_ago = timezone.now() - timedelta(days=7)
    fortnight_ago = timezone.now() - timedelta(days=14)

    alive_q = Q(subscription_end__isnull=True) | Q(subscription_end__gte=today)
    expired_q = Q(subscription_end__lt=today)

    clients_count = Client.objects.count()
    active_subscriptions = Client.objects.filter(alive_q).count()
    expired_subscriptions = Client.objects.filter(expired_q).count()
    expiring_7 = Client.objects.filter(subscription_end__gte=today, subscription_end__lte=in_7)
    expiring_30 = Client.objects.filter(subscription_end__gte=today, subscription_end__lte=in_30)

    plans_by_slug = {plan.slug: plan for plan in Plan.objects.all()}

    def plan_price(slug):
        plan = plans_by_slug.get(slug)
        return plan.price if plan else 0

    def plan_name(slug):
        plan = plans_by_slug.get(slug)
        return plan.name if plan else (slug or 'Sin plan')

    estimated_monthly_revenue = sum(
        plan_price(slug)
        for slug in Client.objects.filter(alive_q).values_list('subscription_type', flat=True)
    )
    revenue_at_risk = sum(
        plan_price(slug)
        for slug in expiring_30.values_list('subscription_type', flat=True)
    )

    plan_mix = []
    for row in Client.objects.values('subscription_type').annotate(count=Count('id')).order_by('-count'):
        slug = row['subscription_type']
        plan_mix.append({
            'slug': slug,
            'name': plan_name(slug),
            'count': row['count'],
            'price': plan_price(slug),
        })

    clients_with_routine = Client.objects.filter(client_routines__is_active=True).distinct().count()
    sessions_7_days = RoutineProgress.objects.filter(completed_at__gte=week_ago).count()
    active_clients_7_days = (
        RoutineProgress.objects.filter(completed_at__gte=week_ago)
        .values('client_routine__client')
        .distinct()
        .count()
    )
    engagement_7_days = round((active_clients_7_days / clients_count) * 100) if clients_count else 0

    trained_14_ids = set(
        RoutineProgress.objects.filter(completed_at__gte=fortnight_ago)
        .values_list('client_routine__client_id', flat=True)
    )
    inactive_subscribers = list(
        Client.objects.filter(alive_q).exclude(id__in=trained_14_ids).order_by('name')
    )

    measured_30_ids = set(
        ProgressMetrics.objects.filter(date__gte=ago_30).values_list('client_id', flat=True)
    )
    clients_without_metrics_30 = Client.objects.filter(alive_q).exclude(id__in=measured_30_ids).count()

    goal_stats = Goal.objects.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(is_completed=True)),
        overdue=Count('id', filter=Q(is_completed=False, deadline__lt=today)),
        on_track=Count('id', filter=Q(is_completed=False, deadline__gte=today)),
    )
    progress_avg = Goal.objects.filter(is_completed=False, deadline__gte=today).exclude(target_value=0).aggregate(
        average_progress=Avg(
            ExpressionWrapper(
                F('current_value') * 100.0 / F('target_value'),
                output_field=FloatField(),
            )
        )
    )['average_progress']

    recent_metrics = list(
        ProgressMetrics.objects.select_related('client')
        .order_by('-date')
        .values('id', 'client_id', 'client__name', 'weight', 'date')[:5]
    )
    recent_sessions = list(
        RoutineProgress.objects.select_related('client_routine__client', 'workout')
        .order_by('-completed_at')
        .values(
            'id',
            'client_routine__client_id',
            'client_routine__client__name',
            'workout__name',
            'started_at',
            'completed_at',
        )[:8]
    )
    recent_goals = list(
        Goal.objects.select_related('client')
        .order_by('-deadline')
        .values(
            'id',
            'client__name',
            'title',
            'current_value',
            'target_value',
            'unit',
            'deadline',
            'is_completed',
        )[:5]
    )

    body_trend = list(
        ProgressMetrics.objects.values('date')
        .annotate(
            weight=Avg('weight'),
            body_fat=Avg('body_fat'),
            muscle_mass=Avg('muscle_mass'),
        )
        .order_by('date')
    )

    session_days = {
        row['day']: row['total']
        for row in (
            RoutineProgress.objects.filter(completed_at__date__gte=ago_14)
            .annotate(day=TruncDate('completed_at'))
            .values('day')
            .annotate(total=Count('id'))
        )
        if row['day']
    }
    sessions_trend = []
    cursor = ago_14
    while cursor <= today:
        sessions_trend.append({
            'date': cursor.isoformat(),
            'sessions': session_days.get(cursor, 0),
        })
        cursor += timedelta(days=1)

    return Response({
        'clients_count': clients_count,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'expiring_7_days': expiring_7.count(),
        'expiring_30_days': expiring_30.count(),
        'estimated_monthly_revenue': estimated_monthly_revenue,
        'revenue_at_risk_30_days': revenue_at_risk,
        'new_clients_7_days': Client.objects.filter(join_date__gte=ago_7).count(),
        'new_clients_30_days': Client.objects.filter(join_date__gte=ago_30).count(),
        'active_routines': ClientRoutine.objects.filter(is_active=True).count(),
        'clients_with_routine': clients_with_routine,
        'clients_without_routine': max(clients_count - clients_with_routine, 0),
        'sessions_7_days': sessions_7_days,
        'active_clients_7_days': active_clients_7_days,
        'engagement_7_days': engagement_7_days,
        'clients_without_metrics_30_days': clients_without_metrics_30,
        'completed_goals': goal_stats['completed'],
        'goals_count': goal_stats['total'],
        'goals_overdue': goal_stats['overdue'],
        'goals_on_track': goal_stats['on_track'],
        'average_progress': round(progress_avg or 0),
        'plan_mix': plan_mix,
        'expiring_clients': [
            {
                'id': client.id,
                'name': client.name,
                'plan_name': plan_name(client.subscription_type),
                'subscription_end': client.subscription_end,
                'price': plan_price(client.subscription_type),
            }
            for client in expiring_30.order_by('subscription_end')
        ],
        'inactive_subscribers': [
            {
                'id': client.id,
                'name': client.name,
                'plan_name': plan_name(client.subscription_type),
            }
            for client in inactive_subscribers
        ],
        'body_trend': [
            {
                'date': item['date'].isoformat() if item['date'] else None,
                'weight': round(item['weight'], 1) if item['weight'] is not None else None,
                'body_fat': round(item['body_fat'], 1) if item['body_fat'] is not None else None,
                'muscle_mass': round(item['muscle_mass'], 1) if item['muscle_mass'] is not None else None,
            }
            for item in body_trend
            if item['date']
        ],
        'sessions_trend': sessions_trend,
        'recent_metrics': [
            {
                'id': item['id'],
                'client_id': item['client_id'],
                'client_name': item['client__name'],
                'weight': item['weight'],
                'date': item['date'],
            }
            for item in recent_metrics
        ],
        'recent_sessions': [
            {
                'id': item['id'],
                'client_id': item['client_routine__client_id'],
                'client_name': item['client_routine__client__name'],
                'workout_name': item['workout__name'],
                'started_at': item['started_at'],
                'completed_at': item['completed_at'],
            }
            for item in recent_sessions
        ],
        'recent_goals': [
            {
                'id': item['id'],
                'client_name': item['client__name'],
                'title': item['title'],
                'current_value': item['current_value'],
                'target_value': item['target_value'],
                'unit': item['unit'],
                'deadline': item['deadline'],
                'is_completed': item['is_completed'],
            }
            for item in recent_goals
        ],
    })


dashboard_summary.cls.required_roles = STAFF_ROLES
