from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet, ExerciseViewSet, WorkoutViewSet, WorkoutSetViewSet,
    RoutineViewSet, ClientRoutineViewSet, RoutineProgressViewSet,
    ProgressMetricsViewSet, GoalViewSet
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'workouts', WorkoutViewSet)
router.register(r'workout-sets', WorkoutSetViewSet)
router.register(r'routines', RoutineViewSet)
router.register(r'client-routines', ClientRoutineViewSet)
router.register(r'routine-progress', RoutineProgressViewSet)
router.register(r'progress-metrics', ProgressMetricsViewSet)
router.register(r'goals', GoalViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
] 