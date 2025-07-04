export interface Client {
  id: string
  name: string
  email: string
  phone: string
  age: number
  weight: number
  height: number
  goals: string[]
  joinDate: Date
  profileImage?: string
  subscription?: {
    type: 'standard' | 'premium' | 'personalized'
    startDate: string
    endDate: string
  }
  assignedRoutines?: string[]
  notes?: string
  emergencyContact?: string
  medicalConditions?: string
}

export interface Exercise {
  id: string
  name: string
  description: string
  muscleGroups: string[]
  equipment: string[]
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  instructions: string[]
  videoUrl?: string
  imageUrl?: string
}

export interface WorkoutSet {
  id: string
  exerciseId: string
  reps: number
  weight: number
  restTime: number // in seconds
  completed: boolean
}

export interface Workout {
  id: string
  name: string
  description: string
  exercises: WorkoutSet[]
  estimatedDuration: number // in minutes
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  category: 'strength' | 'cardio' | 'flexibility' | 'mixed'
}

export interface Routine {
  id: string
  name: string
  description: string
  workouts: Workout[]
  frequency: 'daily' | 'weekly' | 'custom'
  daysPerWeek: number
  duration: number // in weeks
  scheduledDays?: string[] // Array of day names: ['monday', 'wednesday', 'friday']
}

export interface ClientRoutine {
  id: string
  clientId: string
  routineId: string
  startDate: Date
  endDate?: Date
  isActive: boolean
  assignedDays: string[] // Days when this client should do this routine
  progress: RoutineProgress[]
}

export interface RoutineProgress {
  id: string
  clientRoutineId: string
  workoutId: string
  completedAt: Date
  sets: WorkoutSet[]
  notes?: string
  rating?: number // 1-5 stars
}

export interface ProgressMetrics {
  clientId: string
  date: Date
  weight: number
  bodyFat?: number
  muscleMass?: number
  measurements: {
    chest: number
    waist: number
    biceps: number
    forearms: number
    thighs: number
    calves: number
    neck: number
    shoulders: number
    hips: number
  }
  photos?: string[]
}

export interface Goal {
  id: string
  clientId: string
  title: string
  description: string
  targetValue: number
  currentValue: number
  unit: string
  deadline: Date
  isCompleted: boolean
  category: 'weight' | 'strength' | 'endurance' | 'flexibility' | 'custom'
} 