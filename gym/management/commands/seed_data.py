from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from gym.models import (
    Client, Exercise, Workout, WorkoutSet, Routine, 
    ClientRoutine, RoutineProgress, ProgressMetrics, Goal
)

class Command(BaseCommand):
    help = 'Poblar la base de datos con datos iniciales'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando población de datos...')
        
        # Limpiar datos existentes
        self.stdout.write('Limpiando datos existentes...')
        Goal.objects.all().delete()
        ProgressMetrics.objects.all().delete()
        RoutineProgress.objects.all().delete()
        ClientRoutine.objects.all().delete()
        WorkoutSet.objects.all().delete()
        Workout.objects.all().delete()
        Routine.objects.all().delete()
        Exercise.objects.all().delete()
        Client.objects.all().delete()
        
        # Crear ejercicios
        self.stdout.write('Creando ejercicios...')
        exercises = self.create_exercises()
        
        # Crear workouts
        self.stdout.write('Creando workouts...')
        workouts = self.create_workouts(exercises)
        
        # Crear rutinas
        self.stdout.write('Creando rutinas...')
        routines = self.create_routines(workouts)
        
        # Crear clientes
        self.stdout.write('Creando clientes...')
        clients = self.create_clients(routines)
        
        # Crear métricas de progreso
        self.stdout.write('Creando métricas de progreso...')
        self.create_progress_metrics(clients)
        
        # Crear objetivos
        self.stdout.write('Creando objetivos...')
        self.create_goals(clients)
        
        # Crear rutinas de clientes
        self.stdout.write('Creando rutinas de clientes...')
        self.create_client_routines(clients, routines)
        
        self.stdout.write(
            self.style.SUCCESS('¡Datos poblados exitosamente!')
        )

    def create_exercises(self):
        exercises_data = [
            {
                'name': 'Sentadillas',
                'description': 'Ejercicio compuesto para piernas y glúteos',
                'muscle_groups': ['Cuádriceps', 'Glúteos', 'Isquiotibiales'],
                'equipment': ['Peso corporal', 'Barra', 'Mancuernas'],
                'difficulty': 'beginner',
                'instructions': [
                    'Ponte de pie con los pies separados al ancho de los hombros',
                    'Baja el cuerpo como si te sentaras en una silla',
                    'Mantén el pecho arriba y las rodillas alineadas con los dedos',
                    'Vuelve a la posición inicial'
                ],
                'video_url': 'https://example.com/sentadillas.mp4'
            },
            {
                'name': 'Press de Banca',
                'description': 'Ejercicio para pecho, hombros y tríceps',
                'muscle_groups': ['Pectorales', 'Deltoides', 'Tríceps'],
                'equipment': ['Barra', 'Banco'],
                'difficulty': 'intermediate',
                'instructions': [
                    'Acuéstate en el banco con los pies en el suelo',
                    'Agarra la barra con un agarre ligeramente más ancho que los hombros',
                    'Baja la barra controladamente hacia el pecho',
                    'Empuja la barra hacia arriba hasta la posición inicial'
                ]
            },
            {
                'name': 'Peso Muerto',
                'description': 'Ejercicio compuesto para espalda y piernas',
                'muscle_groups': ['Espalda baja', 'Glúteos', 'Isquiotibiales'],
                'equipment': ['Barra'],
                'difficulty': 'advanced',
                'instructions': [
                    'Ponte de pie con los pies separados al ancho de las caderas',
                    'Agarra la barra con las manos separadas al ancho de los hombros',
                    'Mantén la espalda recta y levanta la barra',
                    'Baja la barra controladamente'
                ]
            },
            {
                'name': 'Flexiones',
                'description': 'Ejercicio de peso corporal para pecho y brazos',
                'muscle_groups': ['Pectorales', 'Tríceps', 'Deltoides'],
                'equipment': ['Peso corporal'],
                'difficulty': 'beginner',
                'instructions': [
                    'Colócate en posición de plancha',
                    'Baja el cuerpo hasta que el pecho toque el suelo',
                    'Empuja hacia arriba hasta la posición inicial',
                    'Mantén el cuerpo en línea recta'
                ]
            },
            {
                'name': 'Plancha',
                'description': 'Ejercicio isométrico para core',
                'muscle_groups': ['Abdominales', 'Lumbares'],
                'equipment': ['Peso corporal'],
                'difficulty': 'beginner',
                'instructions': [
                    'Colócate en posición de plancha con los antebrazos en el suelo',
                    'Mantén el cuerpo en línea recta',
                    'Contrae los abdominales',
                    'Mantén la posición durante el tiempo indicado'
                ]
            }
        ]
        
        exercises = []
        for data in exercises_data:
            exercise = Exercise.objects.create(**data)
            exercises.append(exercise)
        
        return exercises

    def create_workouts(self, exercises):
        workouts_data = [
            {
                'name': 'Entrenamiento de Fuerza - Piernas',
                'description': 'Rutina enfocada en desarrollar fuerza en las piernas',
                'estimated_duration': 45,
                'difficulty': 'intermediate',
                'category': 'strength',
                'sets_data': [
                    {'exercise': exercises[0], 'reps': 12, 'weight': 0, 'rest_time': 60, 'completed': False},
                    {'exercise': exercises[2], 'reps': 8, 'weight': 60, 'rest_time': 90, 'completed': False},
                    {'exercise': exercises[4], 'reps': 1, 'weight': 0, 'rest_time': 45, 'completed': False}
                ]
            },
            {
                'name': 'Entrenamiento de Fuerza - Tren Superior',
                'description': 'Rutina para desarrollar fuerza en pecho, espalda y brazos',
                'estimated_duration': 40,
                'difficulty': 'intermediate',
                'category': 'strength',
                'sets_data': [
                    {'exercise': exercises[1], 'reps': 10, 'weight': 40, 'rest_time': 90, 'completed': False},
                    {'exercise': exercises[3], 'reps': 15, 'weight': 0, 'rest_time': 60, 'completed': False},
                    {'exercise': exercises[4], 'reps': 1, 'weight': 0, 'rest_time': 45, 'completed': False}
                ]
            },
            {
                'name': 'Entrenamiento Funcional',
                'description': 'Rutina completa para mejorar la condición física general',
                'estimated_duration': 30,
                'difficulty': 'beginner',
                'category': 'mixed',
                'sets_data': [
                    {'exercise': exercises[0], 'reps': 15, 'weight': 0, 'rest_time': 30, 'completed': False},
                    {'exercise': exercises[3], 'reps': 12, 'weight': 0, 'rest_time': 30, 'completed': False},
                    {'exercise': exercises[4], 'reps': 1, 'weight': 0, 'rest_time': 30, 'completed': False}
                ]
            }
        ]
        
        workouts = []
        for data in workouts_data:
            sets_data = data.pop('sets_data')
            workout = Workout.objects.create(**data)
            
            for set_data in sets_data:
                WorkoutSet.objects.create(workout=workout, **set_data)
            
            workouts.append(workout)
        
        return workouts

    def create_routines(self, workouts):
        routines_data = [
            {
                'name': 'Rutina Principiante - 4 Semanas',
                'description': 'Programa de entrenamiento para principiantes que quieren empezar su viaje fitness',
                'frequency': 'weekly',
                'days_per_week': 3,
                'duration': 4,
                'scheduled_days': ['monday', 'wednesday', 'friday'],
                'workouts': [workouts[2], workouts[0]]
            },
            {
                'name': 'Rutina Intermedia - 8 Semanas',
                'description': 'Programa de entrenamiento para personas con experiencia que buscan mejorar su fuerza',
                'frequency': 'weekly',
                'days_per_week': 4,
                'duration': 8,
                'scheduled_days': ['tuesday', 'thursday', 'saturday', 'sunday'],
                'workouts': [workouts[0], workouts[1]]
            },
            {
                'name': 'Rutina Avanzada - 12 Semanas',
                'description': 'Programa intensivo para atletas experimentados que buscan maximizar su rendimiento',
                'frequency': 'weekly',
                'days_per_week': 5,
                'duration': 12,
                'scheduled_days': ['monday', 'tuesday', 'wednesday', 'friday', 'saturday'],
                'workouts': [workouts[0], workouts[1], workouts[2]]
            }
        ]
        
        routines = []
        for data in routines_data:
            workouts_list = data.pop('workouts')
            routine = Routine.objects.create(**data)
            routine.workouts.set(workouts_list)
            routines.append(routine)
        
        return routines

    def create_clients(self, routines):
        clients_data = [
            {
                'name': 'María González',
                'email': 'maria.gonzalez@email.com',
                'phone': '+34 612 345 678',
                'age': 28,
                'weight': 65,
                'height': 165,
                'goals': ['Perder peso', 'Tonificar músculos', 'Mejorar resistencia'],
                'join_date': date(2024, 1, 15),
                'profile_image': 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face',
                'subscription_type': 'premium',
                'subscription_start': date(2025, 1, 1),
                'subscription_end': date(2025, 6, 1),
                'notes': 'Cliente muy comprometida con sus entrenamientos',
                'emergency_contact': 'Juan González - +34 612 345 679',
                'medical_conditions': 'Ninguna',
                'assigned_routines': [routines[0], routines[1]]
            },
            {
                'name': 'Carlos Rodríguez',
                'email': 'carlos.rodriguez@email.com',
                'phone': '+34 623 456 789',
                'age': 32,
                'weight': 80,
                'height': 180,
                'goals': ['Ganar masa muscular', 'Aumentar fuerza', 'Mejorar composición corporal'],
                'join_date': date(2024, 2, 1),
                'profile_image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
                'subscription_type': 'personalized',
                'subscription_start': date(2025, 1, 15),
                'subscription_end': date(2025, 6, 15),
                'notes': 'Preferencia por entrenamientos de fuerza',
                'emergency_contact': 'Ana Rodríguez - +34 623 456 788',
                'medical_conditions': 'Lesión antigua en rodilla derecha',
                'assigned_routines': [routines[1], routines[2]]
            },
            {
                'name': 'Ana Martínez',
                'email': 'ana.martinez@email.com',
                'phone': '+34 634 567 890',
                'age': 25,
                'weight': 58,
                'height': 160,
                'goals': ['Mantener peso', 'Mejorar flexibilidad', 'Reducir estrés'],
                'join_date': date(2024, 1, 20),
                'profile_image': 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face',
                'subscription_type': 'standard',
                'subscription_start': date(2025, 2, 1),
                'subscription_end': date(2025, 7, 1),
                'notes': 'Interesada en yoga y pilates',
                'emergency_contact': 'Pedro Martínez - +34 634 567 889',
                'medical_conditions': 'Ninguna',
                'assigned_routines': [routines[0]]
            }
        ]
        
        clients = []
        for data in clients_data:
            assigned_routines = data.pop('assigned_routines')
            client = Client.objects.create(**data)
            client.assigned_routines.set(assigned_routines)
            clients.append(client)
        
        return clients

    def create_progress_metrics(self, clients):
        metrics_data = [
            # María González
            {
                'client': clients[0],
                'date': date(2024, 1, 15),
                'weight': 65,
                'body_fat': 25,
                'muscle_mass': 45,
                'measurements': {
                    'chest': 85, 'waist': 70, 'biceps': 28, 'forearms': 25,
                    'thighs': 55, 'calves': 35, 'neck': 35, 'shoulders': 95, 'hips': 90
                }
            },
            {
                'client': clients[0],
                'date': date(2024, 2, 15),
                'weight': 63,
                'body_fat': 23,
                'muscle_mass': 46,
                'measurements': {
                    'chest': 84, 'waist': 68, 'biceps': 29, 'forearms': 26,
                    'thighs': 56, 'calves': 36, 'neck': 35, 'shoulders': 96, 'hips': 88
                }
            },
            # Carlos Rodríguez
            {
                'client': clients[1],
                'date': date(2024, 2, 1),
                'weight': 80,
                'body_fat': 18,
                'muscle_mass': 62,
                'measurements': {
                    'chest': 105, 'waist': 85, 'biceps': 35, 'forearms': 32,
                    'thighs': 65, 'calves': 40, 'neck': 40, 'shoulders': 115, 'hips': 100
                }
            },
            {
                'client': clients[1],
                'date': date(2024, 3, 1),
                'weight': 82,
                'body_fat': 17,
                'muscle_mass': 64,
                'measurements': {
                    'chest': 107, 'waist': 84, 'biceps': 36, 'forearms': 33,
                    'thighs': 66, 'calves': 41, 'neck': 40, 'shoulders': 117, 'hips': 99
                }
            },
            # Ana Martínez
            {
                'client': clients[2],
                'date': date(2024, 1, 20),
                'weight': 58,
                'body_fat': 22,
                'muscle_mass': 42,
                'measurements': {
                    'chest': 80, 'waist': 65, 'biceps': 25, 'forearms': 22,
                    'thighs': 50, 'calves': 32, 'neck': 32, 'shoulders': 88, 'hips': 85
                }
            },
            {
                'client': clients[2],
                'date': date(2024, 2, 20),
                'weight': 58,
                'body_fat': 21,
                'muscle_mass': 43,
                'measurements': {
                    'chest': 81, 'waist': 64, 'biceps': 26, 'forearms': 23,
                    'thighs': 51, 'calves': 33, 'neck': 32, 'shoulders': 89, 'hips': 84
                }
            }
        ]
        
        for data in metrics_data:
            ProgressMetrics.objects.create(**data)

    def create_goals(self, clients):
        goals_data = [
            {
                'client': clients[0],
                'title': 'Perder 5kg',
                'description': 'Reducir peso corporal de forma saludable',
                'target_value': 60,
                'current_value': 65,
                'unit': 'kg',
                'deadline': date(2024, 6, 1),
                'is_completed': False,
                'category': 'weight'
            },
            {
                'client': clients[1],
                'title': 'Aumentar Press de Banca',
                'description': 'Mejorar la fuerza en press de banca',
                'target_value': 100,
                'current_value': 80,
                'unit': 'kg',
                'deadline': date(2024, 8, 1),
                'is_completed': False,
                'category': 'strength'
            },
            {
                'client': clients[2],
                'title': 'Mantener Peso Actual',
                'description': 'Mantener el peso corporal en 58kg',
                'target_value': 58,
                'current_value': 58,
                'unit': 'kg',
                'deadline': date(2024, 12, 1),
                'is_completed': True,
                'category': 'weight'
            }
        ]
        
        for data in goals_data:
            Goal.objects.create(**data)

    def create_client_routines(self, clients, routines):
        client_routines_data = [
            {
                'client': clients[0],
                'routine': routines[0],
                'start_date': date(2024, 1, 15),
                'end_date': date(2024, 2, 15),
                'is_active': True,
                'assigned_days': ['monday', 'wednesday', 'friday']
            },
            {
                'client': clients[1],
                'routine': routines[1],
                'start_date': date(2024, 2, 1),
                'end_date': date(2024, 4, 1),
                'is_active': True,
                'assigned_days': ['tuesday', 'thursday', 'saturday']
            },
            {
                'client': clients[2],
                'routine': routines[0],
                'start_date': date(2024, 1, 20),
                'end_date': date(2024, 2, 20),
                'is_active': True,
                'assigned_days': ['monday', 'wednesday', 'friday']
            }
        ]
        
        for data in client_routines_data:
            ClientRoutine.objects.create(**data) 