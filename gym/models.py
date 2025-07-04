from django.db import models

# Create your models here.

class Client(models.Model):
    SUBSCRIPTION_CHOICES = [
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('personalized', 'Personalized'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30)
    age = models.PositiveIntegerField()
    weight = models.FloatField()
    height = models.FloatField()
    goals = models.JSONField(default=list)
    join_date = models.DateField()
    profile_image = models.URLField(null=True, blank=True)
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, null=True, blank=True)
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)
    assigned_routines = models.ManyToManyField('Routine', blank=True, related_name='clients')
    notes = models.TextField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, null=True, blank=True)
    medical_conditions = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class Exercise(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    muscle_groups = models.JSONField(default=list)
    equipment = models.JSONField(default=list)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    instructions = models.JSONField(default=list)
    video_url = models.URLField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name

class Workout(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    CATEGORY_CHOICES = [
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility'),
        ('mixed', 'Mixed'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    estimated_duration = models.PositiveIntegerField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.name

class WorkoutSet(models.Model):
    workout = models.ForeignKey(Workout, related_name='sets', on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    reps = models.PositiveIntegerField()
    weight = models.FloatField()
    rest_time = models.PositiveIntegerField()
    completed = models.BooleanField(default=False)

class Routine(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('custom', 'Custom'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    workouts = models.ManyToManyField(Workout, related_name='routines')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    days_per_week = models.PositiveIntegerField()
    duration = models.PositiveIntegerField(help_text='Duration in weeks')
    scheduled_days = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return self.name

class ClientRoutine(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    assigned_days = models.JSONField(default=list)

class RoutineProgress(models.Model):
    client_routine = models.ForeignKey(ClientRoutine, on_delete=models.CASCADE)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    completed_at = models.DateTimeField()
    notes = models.TextField(null=True, blank=True)
    rating = models.PositiveIntegerField(null=True, blank=True)

class ProgressMetrics(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date = models.DateField()
    weight = models.FloatField()
    body_fat = models.FloatField(null=True, blank=True)
    muscle_mass = models.FloatField(null=True, blank=True)
    measurements = models.JSONField(default=dict)
    photos = models.JSONField(default=list, null=True, blank=True)

class Goal(models.Model):
    CATEGORY_CHOICES = [
        ('weight', 'Weight'),
        ('strength', 'Strength'),
        ('endurance', 'Endurance'),
        ('flexibility', 'Flexibility'),
        ('custom', 'Custom'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    target_value = models.FloatField()
    current_value = models.FloatField()
    unit = models.CharField(max_length=20)
    deadline = models.DateField()
    is_completed = models.BooleanField(default=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.title
