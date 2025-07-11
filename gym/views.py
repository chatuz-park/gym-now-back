from django.shortcuts import render
from django.db import models
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .filters import ClientFilter, RoutineFilter, ExerciseFilter, WorkoutFilter
from .models import (
    Client, Exercise, Workout, WorkoutSet, Routine, 
    ClientRoutine, RoutineProgress, ProgressMetrics, Goal
)
from .serializers import (
    ClientSerializer, ExerciseSerializer, WorkoutSerializer, WorkoutSetSerializer,
    RoutineSerializer, ClientRoutineSerializer, RoutineProgressSerializer,
    ProgressMetricsSerializer, GoalSerializer, WorkoutCreateSerializer, RoutineCreateSerializer,
    UserProfileSerializer
)

# Create your views here.

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ClientFilter
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'join_date', 'birth_date', 'weight', 'height']
    ordering = ['-join_date']  # Más reciente primero

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
                description="Búsqueda en nombre, email y teléfono",
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
        progress = ProgressMetrics.objects.filter(client=client).order_by('-date')
        serializer = ProgressMetricsSerializer(progress, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def goals(self, request, pk=None):
        """Obtener los objetivos de un cliente específico"""
        client = self.get_object()
        goals = Goal.objects.filter(client=client)
        serializer = GoalSerializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def routines(self, request, pk=None):
        """Obtener las rutinas asignadas a un cliente, incluyendo días asignados y detalles de la asignación"""
        client = self.get_object()
        # Usar el serializer de detalle de asignación
        from .serializers import ClientRoutineDetailSerializer
        assignments = client.client_routines.filter(is_active=True)
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
        
        # Estadísticas por tipo de suscripción
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Obtener los datos del cliente autenticado"""
        try:
            # Obtener el cliente asociado al usuario autenticado
            client = request.user.client_profile
            serializer = self.get_serializer(client)
            return Response(serializer.data)
        except:
            return Response(
                {'error': 'No se encontró perfil de cliente para este usuario'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ExerciseFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'difficulty']
    ordering = ['name']

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

class WorkoutViewSet(viewsets.ModelViewSet):
    queryset = Workout.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WorkoutFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'difficulty', 'estimated_duration']
    ordering = ['name']

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

class WorkoutSetViewSet(viewsets.ModelViewSet):
    queryset = WorkoutSet.objects.all()
    serializer_class = WorkoutSetSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['workout', 'exercise', 'completed']
    ordering_fields = ['reps', 'weight', 'rest_time']
    ordering = ['-id']  # Más reciente primero

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

class RoutineViewSet(viewsets.ModelViewSet):
    queryset = Routine.objects.all()
    serializer_class = RoutineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RoutineFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'duration', 'days_per_week', 'frequency']
    ordering = ['name']

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

class ClientRoutineViewSet(viewsets.ModelViewSet):
    queryset = ClientRoutine.objects.all()
    serializer_class = ClientRoutineSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'routine', 'is_active', 'start_date']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']

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
        progress = RoutineProgress.objects.filter(client_routine=client_routine)
        serializer = RoutineProgressSerializer(progress, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete_workout(self, request, pk=None):
        """Marcar un workout como completado"""
        client_routine = self.get_object()
        workout_id = request.data.get('workout_id')
        notes = request.data.get('notes', '')
        rating = request.data.get('rating', None)
        
        try:
            workout = Workout.objects.get(id=workout_id)
            progress = RoutineProgress.objects.create(
                client_routine=client_routine,
                workout=workout,
                notes=notes,
                rating=rating
            )
            serializer = RoutineProgressSerializer(progress)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Workout.DoesNotExist:
            return Response(
                {'error': 'Workout no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class RoutineProgressViewSet(viewsets.ModelViewSet):
    queryset = RoutineProgress.objects.all()
    serializer_class = RoutineProgressSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client_routine', 'workout', 'completed_at']
    ordering_fields = ['completed_at', 'rating']
    ordering = ['-completed_at']

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

class ProgressMetricsViewSet(viewsets.ModelViewSet):
    queryset = ProgressMetrics.objects.all()
    serializer_class = ProgressMetricsSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'date']
    ordering_fields = ['date', 'weight', 'body_fat', 'muscle_mass']
    ordering = ['-date']

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
        
        progress = self.queryset.filter(client_id=client_id).order_by('-date')
        serializer = self.get_serializer(progress, many=True)
        return Response(serializer.data)

class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'category', 'is_completed', 'deadline']
    search_fields = ['title', 'description']
    ordering_fields = ['deadline', 'target_value', 'current_value']
    ordering = ['deadline']  # Más urgente primero (deadline ascendente)

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
        goals = self.queryset.filter(is_completed=True)
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Obtener objetivos pendientes"""
        goals = self.queryset.filter(is_completed=False)
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
    
    # Verificar que el usuario tenga un perfil de cliente
    try:
        client = user.client_profile
    except:
        return Response(
            {'error': 'Usuario no tiene perfil de cliente'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Generar tokens JWT
    refresh = RefreshToken.for_user(user)
    
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
        # El usuario ya está autenticado gracias al decorador @permission_classes([IsAuthenticated])
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Error al obtener información del usuario: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
