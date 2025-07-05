from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Client, Exercise, Workout, WorkoutSet, Routine, 
    ClientRoutine, RoutineProgress, ProgressMetrics, Goal
)
from .serializers import (
    ClientSerializer, ExerciseSerializer, WorkoutSerializer, WorkoutSetSerializer,
    RoutineSerializer, ClientRoutineSerializer, RoutineProgressSerializer,
    ProgressMetricsSerializer, GoalSerializer, WorkoutCreateSerializer
)

# Create your views here.

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subscription_type', 'age', 'join_date']
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'join_date', 'age', 'weight']
    ordering = ['name']

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
        """Obtener las rutinas asignadas a un cliente"""
        client = self.get_object()
        routines = client.assigned_routines
        serializer = RoutineSerializer(routines, many=True)
        return Response(serializer.data)

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['difficulty']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'difficulty']
    ordering = ['name']

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
    filterset_fields = ['difficulty', 'category', 'estimated_duration']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'difficulty', 'estimated_duration']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WorkoutCreateSerializer
        return WorkoutSerializer

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
    ordering = ['id']

class RoutineViewSet(viewsets.ModelViewSet):
    queryset = Routine.objects.all()
    serializer_class = RoutineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['frequency', 'days_per_week', 'duration']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'duration', 'days_per_week']
    ordering = ['name']

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

class ClientRoutineViewSet(viewsets.ModelViewSet):
    queryset = ClientRoutine.objects.all()
    serializer_class = ClientRoutineSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'routine', 'is_active', 'start_date']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']

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

class ProgressMetricsViewSet(viewsets.ModelViewSet):
    queryset = ProgressMetrics.objects.all()
    serializer_class = ProgressMetricsSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'date']
    ordering_fields = ['date', 'weight', 'body_fat', 'muscle_mass']
    ordering = ['-date']

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
    ordering = ['deadline']

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
