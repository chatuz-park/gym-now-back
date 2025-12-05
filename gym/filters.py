import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q, Count
from datetime import date
from .models import Client, Routine, Exercise, Workout, Goal


class ClientFilter(filters.FilterSet):
    # Filtros de búsqueda
    search = django_filters.CharFilter(method='search_filter', label='Buscar')
    
    # Filtros de edad (calculada dinámicamente)
    min_age = django_filters.NumberFilter(method='filter_min_age', label='Edad mínima')
    max_age = django_filters.NumberFilter(method='filter_max_age', label='Edad máxima')
    age_range = django_filters.RangeFilter(method='filter_age_range', label='Rango de edad')
    
    # Filtros de peso
    weight_range = django_filters.RangeFilter(field_name='weight', label='Rango de peso')
    
    # Filtros de altura
    height_range = django_filters.RangeFilter(field_name='height', label='Rango de altura')
    
    # Filtros de fecha
    join_date_range = django_filters.DateFromToRangeFilter(field_name='join_date', label='Rango de fecha de registro')
    birth_date_range = django_filters.DateFromToRangeFilter(field_name='birth_date', label='Rango de fecha de nacimiento')
    
    # Filtros de suscripción
    subscription_status = django_filters.ChoiceFilter(
        choices=[('active', 'Activa'), ('expired', 'Expirada'), ('none', 'Sin suscripción')],
        method='filter_subscription_status',
        label='Estado de suscripción'
    )
    
    # Filtros de objetivos
    has_goals = django_filters.BooleanFilter(method='filter_has_goals', label='Tiene objetivos')
    
    # Filtros de rutinas asignadas
    has_routines = django_filters.BooleanFilter(method='filter_has_routines', label='Tiene rutinas asignadas')
    routine_count = django_filters.NumberFilter(method='filter_routine_count', label='Número de rutinas')
    
    # Filtro general para diferentes tipos de filtros predefinidos
    filter = django_filters.ChoiceFilter(
        choices=[
            ('all', 'Todos'),
            ('active', 'Activos'),
            ('premium', 'Premium'),
            ('standard', 'Standard'),
            ('personalized', 'Personalizados'),
            ('with-routines', 'Con rutinas'),
            ('without-routines', 'Sin rutinas'),
            ('expiring', 'Por expirar'),
            ('expired', 'Expirados'),
            ('new', 'Nuevos (último mes)'),
        ],
        method='filter_general',
        label='Filtro general'
    )
    
    class Meta:
        model = Client
        fields = {
            'subscription_type': ['exact', 'in'],
            'phone': ['icontains'],
            'emergency_contact': ['icontains'],
            'medical_conditions': ['icontains'],
        }

    def search_filter(self, queryset, name, value):
        """Búsqueda en múltiples campos"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value) |
            Q(emergency_contact__icontains=value)
        )

    def filter_min_age(self, queryset, name, value):
        """Filtro por edad mínima"""
        max_birth_date = date.today().replace(year=date.today().year - int(value))
        return queryset.filter(birth_date__lte=max_birth_date)

    def filter_max_age(self, queryset, name, value):
        """Filtro por edad máxima"""
        min_birth_date = date.today().replace(year=date.today().year - int(value) - 1)
        return queryset.filter(birth_date__gt=min_birth_date)

    def filter_age_range(self, queryset, name, value):
        """Filtro por rango de edad"""
        if value.start is not None:
            max_birth_date = date.today().replace(year=date.today().year - int(value.start))
            queryset = queryset.filter(birth_date__lte=max_birth_date)
        
        if value.stop is not None:
            min_birth_date = date.today().replace(year=date.today().year - int(value.stop) - 1)
            queryset = queryset.filter(birth_date__gt=min_birth_date)
        
        return queryset

    def filter_subscription_status(self, queryset, name, value):
        """Filtro por estado de suscripción"""
        from django.utils import timezone
        
        if value == 'active':
            return queryset.filter(
                Q(subscription_end__isnull=True) | 
                Q(subscription_end__gt=timezone.now().date())
            )
        elif value == 'expired':
            return queryset.filter(subscription_end__lt=timezone.now().date())
        elif value == 'none':
            return queryset.filter(subscription_type__isnull=True)
        
        return queryset

    def filter_has_goals(self, queryset, name, value):
        """Filtro por si tiene objetivos"""
        if value:
            return queryset.filter(goals__isnull=False).exclude(goals=[])
        return queryset.filter(Q(goals__isnull=True) | Q(goals=[]))

    def filter_has_routines(self, queryset, name, value):
        """Filtro por si tiene rutinas asignadas"""
        if value:
            return queryset.filter(client_routines__is_active=True).distinct()
        return queryset.exclude(client_routines__is_active=True)

    def filter_routine_count(self, queryset, name, value):
        """Filtro por número de rutinas asignadas"""
        return queryset.annotate(
            routine_count=Count('client_routines', filter=Q(client_routines__is_active=True))
        ).filter(routine_count=value)

    def filter_general(self, queryset, name, value):
        """Filtro general para diferentes tipos de filtros predefinidos"""
        from django.utils import timezone
        from datetime import timedelta
        
        if value == 'all':
            return queryset
        
        elif value == 'active':
            return queryset.filter(
                Q(subscription_end__isnull=True) | 
                Q(subscription_end__gt=timezone.now().date())
            )
        
        elif value == 'premium':
            return queryset.filter(subscription_type='premium')
        
        elif value == 'standard':
            return queryset.filter(subscription_type='standard')
        
        elif value == 'personalized':
            return queryset.filter(subscription_type='personalized')
        
        elif value == 'with-routines':
            return queryset.filter(client_routines__is_active=True).distinct()
        
        elif value == 'without-routines':
            return queryset.exclude(client_routines__is_active=True)
        
        elif value == 'expiring':
            # Clientes con suscripción que expira en los próximos 30 días
            thirty_days_from_now = timezone.now().date() + timedelta(days=30)
            return queryset.filter(
                subscription_end__isnull=False,
                subscription_end__lte=thirty_days_from_now,
                subscription_end__gt=timezone.now().date()
            )
        
        elif value == 'expired':
            return queryset.filter(subscription_end__lt=timezone.now().date())
        
        elif value == 'new':
            # Clientes registrados en el último mes
            one_month_ago = timezone.now().date() - timedelta(days=30)
            return queryset.filter(join_date__gte=one_month_ago)
        
        return queryset


class RoutineFilter(filters.FilterSet):
    # Filtros de búsqueda
    search = django_filters.CharFilter(method='search_filter', label='Buscar')
    
    # Filtros de duración
    duration_range = django_filters.RangeFilter(field_name='duration', label='Rango de duración')
    
    # Filtros de días por semana
    days_range = django_filters.RangeFilter(field_name='days_per_week', label='Rango de días por semana')
    
    # Filtros de workouts
    workout_count = django_filters.NumberFilter(method='filter_workout_count', label='Número de workouts')
    min_workouts = django_filters.NumberFilter(method='filter_min_workouts', label='Mínimo de workouts')
    max_workouts = django_filters.NumberFilter(method='filter_max_workouts', label='Máximo de workouts')
    
    # Filtros de popularidad
    min_clients = django_filters.NumberFilter(method='filter_min_clients', label='Mínimo de clientes')
    max_clients = django_filters.NumberFilter(method='filter_max_clients', label='Máximo de clientes')
    
    # Filtros de dificultad estimada
    estimated_difficulty = django_filters.ChoiceFilter(
        choices=[('easy', 'Fácil'), ('medium', 'Media'), ('hard', 'Difícil')],
        method='filter_estimated_difficulty',
        label='Dificultad estimada'
    )
    
    # Filtros de categorías de workouts
    workout_categories = django_filters.CharFilter(method='filter_workout_categories', label='Categorías de workouts')
    
    class Meta:
        model = Routine
        fields = {
            'frequency': ['exact', 'in'],
            'days_per_week': ['exact', 'gte', 'lte'],
            'duration': ['exact', 'gte', 'lte'],
        }

    def search_filter(self, queryset, name, value):
        """Búsqueda en múltiples campos"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )

    def filter_workout_count(self, queryset, name, value):
        """Filtro por número exacto de workouts"""
        if value == 0:
            return queryset.filter(workouts__isnull=True)
        return queryset.annotate(
            workout_count=Count('workouts')
        ).filter(workout_count=value)

    def filter_min_workouts(self, queryset, name, value):
        """Filtro por mínimo de workouts"""
        return queryset.annotate(
            workout_count=Count('workouts')
        ).filter(workout_count__gte=value)

    def filter_max_workouts(self, queryset, name, value):
        """Filtro por máximo de workouts"""
        return queryset.annotate(
            workout_count=Count('workouts')
        ).filter(workout_count__lte=value)

    def filter_min_clients(self, queryset, name, value):
        """Filtro por mínimo de clientes asignados"""
        return queryset.annotate(
            client_count=Count('client_routines', filter=Q(client_routines__is_active=True))
        ).filter(client_count__gte=value)

    def filter_max_clients(self, queryset, name, value):
        """Filtro por máximo de clientes asignados"""
        return queryset.annotate(
            client_count=Count('client_routines', filter=Q(client_routines__is_active=True))
        ).filter(client_count__lte=value)

    def filter_estimated_difficulty(self, queryset, name, value):
        """Filtro por dificultad estimada basada en días por semana y duración"""
        if value == 'easy':
            return queryset.filter(days_per_week__lte=3, duration__lte=4)
        elif value == 'medium':
            return queryset.filter(
                Q(days_per_week__range=(4, 5), duration__range=(5, 8)) |
                Q(days_per_week=3, duration__range=(5, 8))
            )
        elif value == 'hard':
            return queryset.filter(
                Q(days_per_week__gte=6) |
                Q(duration__gte=9) |
                Q(days_per_week__gte=5, duration__gte=8)
            )
        return queryset

    def filter_workout_categories(self, queryset, name, value):
        """Filtro por categorías de workouts en la rutina"""
        categories = [cat.strip() for cat in value.split(',')]
        return queryset.filter(workouts__category__in=categories).distinct()


class ExerciseFilter(filters.FilterSet):
    search = django_filters.CharFilter(method='search_filter', label='Buscar')
    muscle_groups = django_filters.CharFilter(method='filter_muscle_groups', label='Grupos musculares')
    equipment = django_filters.CharFilter(method='filter_equipment', label='Equipamiento')
    
    class Meta:
        model = Exercise
        fields = {
            'difficulty': ['exact', 'in'],
            'name': ['icontains'],
            'description': ['icontains'],
        }

    def search_filter(self, queryset, name, value):
        """Búsqueda en múltiples campos"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )

    def filter_muscle_groups(self, queryset, name, value):
        """Filtro por grupos musculares"""
        groups = [group.strip() for group in value.split(',')]
        return queryset.filter(muscle_groups__overlap=groups)

    def filter_equipment(self, queryset, name, value):
        """Filtro por equipamiento"""
        equipment_list = [eq.strip() for eq in value.split(',')]
        return queryset.filter(equipment__overlap=equipment_list)


class WorkoutFilter(filters.FilterSet):
    search = django_filters.CharFilter(method='search_filter', label='Buscar')
    estimated_duration_range = django_filters.RangeFilter(field_name='estimated_duration', label='Rango de duración')
    exercise_count = django_filters.NumberFilter(method='filter_exercise_count', label='Número de ejercicios')
    
    class Meta:
        model = Workout
        fields = {
            'difficulty': ['exact', 'in'],
            'category': ['exact', 'in'],
            'name': ['icontains'],
            'description': ['icontains'],
        }

    def search_filter(self, queryset, name, value):
        """Búsqueda en múltiples campos"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )

    def filter_exercise_count(self, queryset, name, value):
        """Filtro por número de ejercicios"""
        return queryset.annotate(
            exercise_count=Count('sets__exercise', distinct=True)
        ).filter(exercise_count=value)


class GoalFilter(filters.FilterSet):
    search = django_filters.CharFilter(method='search_filter', label='Buscar')
    
    class Meta:
        model = Goal
        fields = {
            'client': ['exact'],
            'category': ['exact', 'in'],
            'is_completed': ['exact'],
            'deadline': ['exact', 'gte', 'lte'],
        }

    def search_filter(self, queryset, name, value):
        """Búsqueda en múltiples campos"""
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value)
        ) 