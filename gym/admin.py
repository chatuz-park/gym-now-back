from django.contrib import admin
from django.utils import timezone
from .models import (
    CustomUser, Client, Exercise, Workout, WorkoutSet, Routine, 
    ClientRoutine, RoutineProgress, ProgressMetrics, Goal
)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'user_email', 'user_full_name']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    user_full_name.short_description = 'Nombre Completo'

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'age', 'subscription_type', 'join_date', 'is_active']
    list_filter = ['subscription_type', 'join_date', 'birth_date']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['join_date']
    
    def is_active(self, obj):
        return obj.subscription_end is None or obj.subscription_end > timezone.now().date()
    is_active.boolean = True
    is_active.short_description = 'Activo'

    def age(self, obj):
        return obj.age
    age.short_description = 'Edad'

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'difficulty', 'muscle_groups_display', 'equipment_display']
    list_filter = ['difficulty']
    search_fields = ['name', 'description']
    
    def muscle_groups_display(self, obj):
        return ', '.join(obj.muscle_groups) if obj.muscle_groups else '-'
    muscle_groups_display.short_description = 'Grupos Musculares'
    
    def equipment_display(self, obj):
        return ', '.join(obj.equipment) if obj.equipment else '-'
    equipment_display.short_description = 'Equipamiento'

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'difficulty', 'estimated_duration', 'sets_count']
    list_filter = ['category', 'difficulty']
    search_fields = ['name', 'description']
    
    def sets_count(self, obj):
        return obj.sets.count()
    sets_count.short_description = 'Número de Sets'

@admin.register(WorkoutSet)
class WorkoutSetAdmin(admin.ModelAdmin):
    list_display = ['workout', 'exercise', 'reps', 'weight', 'rest_time', 'completed']
    list_filter = ['workout', 'exercise', 'completed']
    search_fields = ['workout__name', 'exercise__name']

@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ['name', 'frequency', 'days_per_week', 'duration', 'workouts_count']
    list_filter = ['frequency', 'days_per_week']
    search_fields = ['name', 'description']
    filter_horizontal = ['workouts']
    
    def workouts_count(self, obj):
        return obj.workouts.count()
    workouts_count.short_description = 'Número de Workouts'

@admin.register(ClientRoutine)
class ClientRoutineAdmin(admin.ModelAdmin):
    list_display = ['client', 'routine', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'start_date', 'routine']
    search_fields = ['client__name', 'routine__name']
    readonly_fields = ['start_date']

@admin.register(RoutineProgress)
class RoutineProgressAdmin(admin.ModelAdmin):
    list_display = ['client_routine', 'workout', 'completed_at', 'rating']
    list_filter = ['completed_at', 'rating', 'client_routine__client']
    search_fields = ['client_routine__client__name', 'workout__name']
    readonly_fields = ['completed_at']

@admin.register(ProgressMetrics)
class ProgressMetricsAdmin(admin.ModelAdmin):
    list_display = ['client', 'date', 'weight', 'body_fat', 'muscle_mass']
    list_filter = ['date', 'client']
    search_fields = ['client__name']
    readonly_fields = ['date']

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['client', 'title', 'category', 'current_value', 'target_value', 'is_completed', 'deadline']
    list_filter = ['category', 'is_completed', 'deadline', 'client']
    search_fields = ['client__name', 'title', 'description']
    readonly_fields = ['is_completed']
    
    def save_model(self, request, obj, form, change):
        obj.is_completed = obj.current_value >= obj.target_value
        super().save_model(request, obj, form, change)
