from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import (
    Client, CustomUser, Exercise, Workout, WorkoutSet, Routine,
    ClientRoutine, RoutineProgress, ProgressMetrics, Goal, Plan
)
from .permissions import get_user_role, is_owner_role

class PlanSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'duration_days',
            'features', 'color', 'is_active', 'subscribers_count',
        ]
        read_only_fields = ['id', 'subscribers_count']
        extra_kwargs = {
            'slug': {'required': False, 'allow_blank': True},
            'description': {'required': False, 'allow_blank': True},
        }

    def get_subscribers_count(self, obj):
        annotated = getattr(obj, 'subscribers_count', None)
        if annotated is not None and not isinstance(annotated, list):
            try:
                return int(annotated)
            except (TypeError, ValueError):
                pass
        return Client.objects.filter(subscription_type=obj.slug).count()

    def validate_features(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Las características deben ser una lista.')
        cleaned = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise serializers.ValidationError('Cada característica debe ser un texto.')
            cleaned.append(item.strip())
        return cleaned

    def validate_duration_days(self, value):
        if value < 1:
            raise serializers.ValidationError('La duración debe ser de al menos 1 día.')
        return value

    def validate(self, attrs):
        instance = self.instance
        is_active = attrs.get('is_active', getattr(instance, 'is_active', True))
        if instance and is_active is False:
            other_active = Plan.objects.filter(is_active=True).exclude(pk=instance.pk).exists()
            if not other_active:
                raise serializers.ValidationError({
                    'detail': 'Debe quedar al menos un plan activo.',
                })

        slug = attrs.get('slug')
        if not slug:
            name = attrs.get('name') or (instance.name if instance else '')
            slug = slugify(name)
            if not slug:
                raise serializers.ValidationError({
                    'detail': 'El código del plan es obligatorio.',
                })
            attrs['slug'] = slug

        if instance and slug != instance.slug:
            if Client.objects.filter(subscription_type=instance.slug).exists():
                raise serializers.ValidationError({
                    'detail': 'No se puede cambiar el código de un plan con clientes asignados.',
                })
        return attrs


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
    username = serializers.CharField(source='user.username', read_only=True)
    default_password = serializers.SerializerMethodField()
    age = serializers.ReadOnlyField()
    plan = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = '__all__'

    def get_default_password(self, obj):
        """Retorna la contraseña por defecto solo para owners."""
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not is_owner_role(get_user_role(user)):
            return None
        if obj.user:
            return obj.generate_default_password()
        return None

    def get_assigned_routines(self, obj):
        """Obtener las asignaciones completas de rutinas con sus detalles"""
        from .serializers import ClientRoutineDetailSerializer
        return ClientRoutineDetailSerializer(obj.client_routines.filter(is_active=True), many=True).data

    def validate_email(self, value):
        """Validar que el email sea único"""
        if Client.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value

    def validate_phone(self, value):
        """Validar que el teléfono sea único"""
        if Client.objects.filter(phone=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Este número de teléfono ya está registrado.")
        return value

    def get_plan(self, obj):
        if not obj.subscription_type:
            return None
        plans = self.context.get('_plans_by_slug')
        if plans is None:
            plans = {plan.slug: plan for plan in Plan.objects.all()}
            self.context['_plans_by_slug'] = plans
        plan = plans.get(obj.subscription_type)
        if plan is None:
            return None
        return PlanSerializer(plan, context=self.context).data

    def validate(self, attrs):
        slug = attrs.get('subscription_type')
        if slug:
            plan = Plan.objects.filter(slug=slug).first()
            if plan is None:
                raise serializers.ValidationError({
                    'detail': f'No existe un plan con código "{slug}".',
                })
            current = getattr(self.instance, 'subscription_type', None)
            if not plan.is_active and slug != current:
                raise serializers.ValidationError({
                    'detail': 'No se puede asignar un plan inactivo.',
                })
        return attrs

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

    def validate_assigned_days(self, value):
        """
        Validar y convertir el formato de assigned_days
        Acepta tanto lista de días como objeto con valores booleanos
        """
        if isinstance(value, dict):
            # Convertir objeto {day: boolean} a lista de días seleccionados
            days_mapping = {
                'monday': 'monday',
                'tuesday': 'tuesday', 
                'wednesday': 'wednesday',
                'thursday': 'thursday',
                'friday': 'friday',
                'saturday': 'saturday',
                'sunday': 'sunday'
            }
            
            selected_days = []
            for day_key, is_selected in value.items():
                if is_selected and day_key in days_mapping:
                    selected_days.append(days_mapping[day_key])
            
            return selected_days
        elif isinstance(value, list):
            # Validar que todos los elementos sean días válidos
            valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in value:
                if day not in valid_days:
                    raise serializers.ValidationError(f"Día inválido: {day}. Días válidos: {', '.join(valid_days)}")
            return value
        else:
            raise serializers.ValidationError("assigned_days debe ser una lista de días o un objeto con valores booleanos")

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
        fields = [
            'id', 'client_routine', 'client_routine_id', 'workout', 'workout_id',
            'started_at', 'completed_at', 'notes', 'rating',
        ]
        read_only_fields = ['id', 'completed_at']

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

class RoutineCreateSerializer(serializers.ModelSerializer):
    workouts = WorkoutCreateSerializer(many=True)

    class Meta:
        model = Routine
        fields = ['name', 'description', 'frequency', 'days_per_week', 'duration', 'workouts']

    def create(self, validated_data):
        workouts_data = validated_data.pop('workouts')
        routine = Routine.objects.create(**validated_data)
        
        for workout_data in workouts_data:
            sets_data = workout_data.pop('sets')
            workout = Workout.objects.create(**workout_data)
            
            # Agregar el workout a la rutina usando la relación many-to-many
            routine.workouts.add(workout)
            
            for set_data in sets_data:
                WorkoutSet.objects.create(workout=workout, **set_data)
        
        return routine

    def update(self, instance, validated_data):
        workouts_data = validated_data.pop('workouts', None)
        
        # Actualizar campos de la rutina
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar workouts si se proporcionan
        if workouts_data is not None:
            # Eliminar workouts existentes de la rutina
            instance.workouts.clear()
            
            # Crear nuevos workouts
            for workout_data in workouts_data:
                sets_data = workout_data.pop('sets')
                workout = Workout.objects.create(**workout_data)
                
                # Agregar el workout a la rutina
                instance.workouts.add(workout)
                
                for set_data in sets_data:
                    WorkoutSet.objects.create(workout=workout, **set_data)
        
        return instance 

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para la información del usuario autenticado"""
    role = serializers.ChoiceField(
        source='custom_profile.role',
        choices=[choice[0] for choice in CustomUser.ROLE_CHOICES],
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'date_joined', 'last_login', 'role'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'role']


class UserRoleAdminSerializer(serializers.ModelSerializer):
    """Listado y cambio de rol. Solo el campo role es escribible."""
    role = serializers.ChoiceField(
        source='custom_profile.role',
        choices=[choice[0] for choice in CustomUser.ROLE_CHOICES],
    )
    client_id = serializers.SerializerMethodField()
    is_last_owner = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'client_id', 'is_last_owner', 'date_joined', 'last_login',
        ]
        read_only_fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'client_id', 'is_last_owner', 'date_joined', 'last_login',
        ]

    def get_client_id(self, obj):
        try:
            return obj.client_profile.id
        except Client.DoesNotExist:
            return None

    def get_is_last_owner(self, obj):
        if get_user_role(obj) != 'owner':
            return False
        if not hasattr(self, '_owner_count'):
            self._owner_count = CustomUser.objects.filter(role='owner').count()
        return self._owner_count <= 1

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get('role'):
            data['role'] = get_user_role(instance) or 'guest'
        return data

    def validate(self, attrs):
        instance = self.instance
        profile_data = attrs.get('custom_profile') or {}
        new_role = profile_data.get('role')
        if instance is None or new_role is None:
            return attrs

        current_role = get_user_role(instance)
        if current_role == 'owner' and new_role != 'owner':
            owner_count = CustomUser.objects.filter(role='owner').count()
            if owner_count <= 1:
                raise serializers.ValidationError({
                    'detail': 'No se puede quitar el rol de propietario al último owner.',
                })
        return attrs

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('custom_profile', {})
        new_role = profile_data.get('role')
        instance = super().update(instance, validated_data)
        if new_role is not None:
            profile, _ = CustomUser.objects.get_or_create(user=instance)
            profile.role = new_role
            profile.save(update_fields=['role'])
            instance.custom_profile = profile
        return instance


class GymTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT de acceso con claims de rol para el contrato RBAC."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = get_user_role(user) or 'guest'
        token['user_id'] = user.id
        return token

class ProfileImageUploadSerializer(serializers.Serializer):
    """Serializer para subida de imagen de perfil"""
    profile_image = serializers.ImageField()


class ExerciseImageUploadSerializer(serializers.Serializer):
    """Serializer para subida de imagen de ejercicio"""
    image = serializers.ImageField() 