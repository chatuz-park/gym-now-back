from rest_framework import serializers
from .models import (
    Client, Exercise, Workout, WorkoutSet, Routine, 
    ClientRoutine, RoutineProgress, ProgressMetrics, Goal
)

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'

class WorkoutSetSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(),
        source='exercise',
        write_only=True
    )

    class Meta:
        model = WorkoutSet
        fields = ['id', 'exercise', 'exercise_id', 'reps', 'weight', 'rest_time', 'completed']

class WorkoutSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, read_only=True)

    class Meta:
        model = Workout
        fields = '__all__'

class RoutineSerializer(serializers.ModelSerializer):
    workouts = WorkoutSerializer(many=True, read_only=True)

    class Meta:
        model = Routine
        fields = '__all__'

class ClientRoutineDetailSerializer(serializers.ModelSerializer):
    """Serializer para mostrar detalles completos de una asignación de rutina"""
    routine = RoutineSerializer(read_only=True)
    
    class Meta:
        model = ClientRoutine
        fields = ['id', 'routine', 'start_date', 'end_date', 'is_active', 'assigned_days']

class ClientSerializer(serializers.ModelSerializer):
    assigned_routines = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = '__all__'

    def get_assigned_routines(self, obj):
        """Obtener las asignaciones completas de rutinas con sus detalles"""
        from .serializers import ClientRoutineDetailSerializer
        return ClientRoutineDetailSerializer(obj.client_routines.filter(is_active=True), many=True).data

class ClientRoutineSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    routine = RoutineSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        source='client',
        write_only=True
    )
    routine_id = serializers.PrimaryKeyRelatedField(
        queryset=Routine.objects.all(),
        source='routine',
        write_only=True
    )

    class Meta:
        model = ClientRoutine
        fields = ['id', 'client', 'client_id', 'routine', 'routine_id', 'start_date', 'end_date', 'is_active', 'assigned_days']

    def validate(self, data):
        """
        Validar que no se asigne la misma rutina al mismo cliente más de una vez
        """
        client = data.get('client')
        routine = data.get('routine')
        
        # Verificar si ya existe una asignación activa para este cliente y rutina
        existing_assignment = ClientRoutine.objects.filter(
            client=client,
            routine=routine,
            is_active=True
        )
        
        # Si estamos actualizando, excluir la instancia actual
        if self.instance:
            existing_assignment = existing_assignment.exclude(pk=self.instance.pk)
        
        if existing_assignment.exists():
            raise serializers.ValidationError(
                f"El cliente '{client.name}' ya tiene asignada la rutina '{routine.name}' de forma activa."
            )
        
        return data

class RoutineProgressSerializer(serializers.ModelSerializer):
    client_routine = ClientRoutineSerializer(read_only=True)
    workout = WorkoutSerializer(read_only=True)
    client_routine_id = serializers.PrimaryKeyRelatedField(
        queryset=ClientRoutine.objects.all(),
        source='client_routine',
        write_only=True
    )
    workout_id = serializers.PrimaryKeyRelatedField(
        queryset=Workout.objects.all(),
        source='workout',
        write_only=True
    )

    class Meta:
        model = RoutineProgress
        fields = ['id', 'client_routine', 'client_routine_id', 'workout', 'workout_id', 'completed_at', 'notes', 'rating']

class ProgressMetricsSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        source='client',
        write_only=True
    )

    class Meta:
        model = ProgressMetrics
        fields = '__all__'

class GoalSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        source='client',
        write_only=True
    )

    class Meta:
        model = Goal
        fields = '__all__'

# Serializers para crear/actualizar con relaciones
class WorkoutSetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSet
        fields = ['exercise', 'reps', 'weight', 'rest_time', 'completed']

class WorkoutCreateSerializer(serializers.ModelSerializer):
    sets = WorkoutSetCreateSerializer(many=True)

    class Meta:
        model = Workout
        fields = ['name', 'description', 'estimated_duration', 'difficulty', 'category', 'sets']

    def create(self, validated_data):
        sets_data = validated_data.pop('sets')
        workout = Workout.objects.create(**validated_data)
        
        for set_data in sets_data:
            WorkoutSet.objects.create(workout=workout, **set_data)
        
        return workout

    def update(self, instance, validated_data):
        sets_data = validated_data.pop('sets', None)
        
        # Actualizar campos del workout
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar sets si se proporcionan
        if sets_data is not None:
            # Eliminar sets existentes
            instance.sets.all().delete()
            # Crear nuevos sets
            for set_data in sets_data:
                WorkoutSet.objects.create(workout=instance, **set_data)
        
        return instance 