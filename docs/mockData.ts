import type { Client, Exercise, Workout, Routine, Goal, ProgressMetrics } from './index'

export const mockClients: Client[] = [
  {
    id: '1',
    name: 'María González',
    email: 'maria.gonzalez@email.com',
    phone: '+34 612 345 678',
    age: 28,
    weight: 65,
    height: 165,
    goals: ['Perder peso', 'Tonificar músculos', 'Mejorar resistencia'],
    joinDate: new Date('2024-01-15'),
    profileImage: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'premium',
      startDate: '2025-01-01',
      endDate: '2025-06-01'
    },
    assignedRoutines: ['1', '2'],
    notes: 'Cliente muy comprometida con sus entrenamientos',
    emergencyContact: 'Juan González - +34 612 345 679',
    medicalConditions: 'Ninguna'
  },
  {
    id: '2',
    name: 'Carlos Rodríguez',
    email: 'carlos.rodriguez@email.com',
    phone: '+34 623 456 789',
    age: 32,
    weight: 80,
    height: 180,
    goals: ['Ganar masa muscular', 'Aumentar fuerza', 'Mejorar composición corporal'],
    joinDate: new Date('2024-02-01'),
    profileImage: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'personalized',
      startDate: '2025-01-15',
      endDate: '2025-06-15'
    },
    assignedRoutines: ['2', '3'],
    notes: 'Preferencia por entrenamientos de fuerza',
    emergencyContact: 'Ana Rodríguez - +34 623 456 788',
    medicalConditions: 'Lesión antigua en rodilla derecha'
  },
  {
    id: '3',
    name: 'Ana Martínez',
    email: 'ana.martinez@email.com',
    phone: '+34 634 567 890',
    age: 25,
    weight: 58,
    height: 160,
    goals: ['Mantener peso', 'Mejorar flexibilidad', 'Reducir estrés'],
    joinDate: new Date('2024-01-20'),
    profileImage: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'standard',
      startDate: '2025-02-01',
      endDate: '2025-07-01'
    },
    assignedRoutines: ['1'],
    notes: 'Interesada en yoga y pilates',
    emergencyContact: 'Pedro Martínez - +34 634 567 889',
    medicalConditions: 'Ninguna'
  },
  {
    id: '4',
    name: 'Luis Fernández',
    email: 'luis.fernandez@email.com',
    phone: '+34 645 678 901',
    age: 35,
    weight: 75,
    height: 175,
    goals: ['Perder grasa', 'Mejorar resistencia cardiovascular', 'Tonificar'],
    joinDate: new Date('2024-03-01'),
    profileImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'premium',
      startDate: '2024-07-01',
      endDate: '2025-10-01'
    },
    assignedRoutines: ['2'],
    notes: 'Cliente nuevo, muy motivado',
    emergencyContact: 'Carmen Fernández - +34 645 678 900',
    medicalConditions: 'Ninguna'
  },
  {
    id: '5',
    name: 'Sofia López',
    email: 'sofia.lopez@email.com',
    phone: '+34 656 789 012',
    age: 29,
    weight: 62,
    height: 168,
    goals: ['Ganar fuerza', 'Mejorar postura', 'Reducir dolor de espalda'],
    joinDate: new Date('2024-02-15'),
    profileImage: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'personalized',
      startDate: '2025-06-01',
      endDate: '2026-06-01'
    },
    assignedRoutines: ['1', '3'],
    notes: 'Necesita ejercicios específicos para la espalda',
    emergencyContact: 'Miguel López - +34 656 789 011',
    medicalConditions: 'Dolor crónico en espalda baja'
  },
  {
    id: '6',
    name: 'David García',
    email: 'david.garcia@email.com',
    phone: '+34 667 890 123',
    age: 27,
    weight: 70,
    height: 172,
    goals: ['Aumentar masa muscular', 'Mejorar rendimiento deportivo'],
    joinDate: new Date('2024-01-10'),
    profileImage: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'standard',
      startDate: '2025-07-01',
      endDate: '2026-07-01'
    },
    assignedRoutines: ['2'],
    notes: 'Jugador de fútbol amateur',
    emergencyContact: 'Elena García - +34 667 890 122',
    medicalConditions: 'Ninguna'
  },
  {
    id: '7',
    name: 'Carmen Ruiz',
    email: 'carmen.ruiz@email.com',
    phone: '+34 678 901 234',
    age: 31,
    weight: 68,
    height: 165,
    goals: ['Perder peso', 'Mejorar autoestima', 'Mantener salud'],
    joinDate: new Date('2024-03-15'),
    profileImage: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'premium',
      startDate: '2025-08-01',
      endDate: '2026-08-01'
    },
    assignedRoutines: ['1', '2'],
    notes: 'Cliente muy dedicada, progreso excelente',
    emergencyContact: 'Javier Ruiz - +34 678 901 233',
    medicalConditions: 'Ninguna'
  },
  {
    id: '8',
    name: 'Roberto Jiménez',
    email: 'roberto.jimenez@email.com',
    phone: '+34 689 012 345',
    age: 40,
    weight: 85,
    height: 178,
    goals: ['Perder peso', 'Mejorar salud cardiovascular', 'Reducir estrés'],
    joinDate: new Date('2024-02-20'),
    profileImage: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'personalized',
      startDate: '2025-09-01',
      endDate: '2026-09-01'
    },
    assignedRoutines: ['3'],
    notes: 'Ejecutivo con poco tiempo, necesita rutinas eficientes',
    emergencyContact: 'Patricia Jiménez - +34 689 012 344',
    medicalConditions: 'Hipertensión controlada'
  },
  {
    id: '9',
    name: 'Laura Torres',
    email: 'laura.torres@email.com',
    phone: '+34 690 123 456',
    age: 26,
    weight: 55,
    height: 162,
    goals: ['Ganar peso saludable', 'Mejorar fuerza', 'Aumentar masa muscular'],
    joinDate: new Date('2024-01-05'),
    profileImage: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'standard',
      startDate: '2025-10-01',
      endDate: '2026-10-01'
    },
    assignedRoutines: ['1'],
    notes: 'Cliente muy delgada, necesita ganar peso de forma saludable',
    emergencyContact: 'Carlos Torres - +34 690 123 455',
    medicalConditions: 'Ninguna'
  },
  {
    id: '10',
    name: 'Miguel Sánchez',
    email: 'miguel.sanchez@email.com',
    phone: '+34 691 234 567',
    age: 33,
    weight: 78,
    height: 176,
    goals: ['Mantener peso', 'Mejorar resistencia', 'Preparar maratón'],
    joinDate: new Date('2024-02-10'),
    profileImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
    subscription: {
      type: 'premium',
      startDate: '2025-11-01',
      endDate: '2026-11-01'
    },
    assignedRoutines: ['2', '3'],
    notes: 'Preparando maratón de Madrid en octubre',
    emergencyContact: 'Isabel Sánchez - +34 691 234 566',
    medicalConditions: 'Ninguna'
  }
]

export const mockExercises: Exercise[] = [
  {
    id: '1',
    name: 'Sentadillas',
    description: 'Ejercicio compuesto para piernas y glúteos',
    muscleGroups: ['Cuádriceps', 'Glúteos', 'Isquiotibiales'],
    equipment: ['Peso corporal', 'Barra', 'Mancuernas'],
    difficulty: 'beginner',
    instructions: [
      'Ponte de pie con los pies separados al ancho de los hombros',
      'Baja el cuerpo como si te sentaras en una silla',
      'Mantén el pecho arriba y las rodillas alineadas con los dedos',
      'Vuelve a la posición inicial'
    ],
    videoUrl: 'https://example.com/sentadillas.mp4'
  },
  {
    id: '2',
    name: 'Press de Banca',
    description: 'Ejercicio para pecho, hombros y tríceps',
    muscleGroups: ['Pectorales', 'Deltoides', 'Tríceps'],
    equipment: ['Barra', 'Banco'],
    difficulty: 'intermediate',
    instructions: [
      'Acuéstate en el banco con los pies en el suelo',
      'Agarra la barra con un agarre ligeramente más ancho que los hombros',
      'Baja la barra controladamente hacia el pecho',
      'Empuja la barra hacia arriba hasta la posición inicial'
    ]
  },
  {
    id: '3',
    name: 'Peso Muerto',
    description: 'Ejercicio compuesto para espalda y piernas',
    muscleGroups: ['Espalda baja', 'Glúteos', 'Isquiotibiales'],
    equipment: ['Barra'],
    difficulty: 'advanced',
    instructions: [
      'Ponte de pie con los pies separados al ancho de las caderas',
      'Agarra la barra con las manos separadas al ancho de los hombros',
      'Mantén la espalda recta y levanta la barra',
      'Baja la barra controladamente'
    ]
  },
  {
    id: '4',
    name: 'Flexiones',
    description: 'Ejercicio de peso corporal para pecho y brazos',
    muscleGroups: ['Pectorales', 'Tríceps', 'Deltoides'],
    equipment: ['Peso corporal'],
    difficulty: 'beginner',
    instructions: [
      'Colócate en posición de plancha',
      'Baja el cuerpo hasta que el pecho toque el suelo',
      'Empuja hacia arriba hasta la posición inicial',
      'Mantén el cuerpo en línea recta'
    ]
  },
  {
    id: '5',
    name: 'Plancha',
    description: 'Ejercicio isométrico para core',
    muscleGroups: ['Abdominales', 'Lumbares'],
    equipment: ['Peso corporal'],
    difficulty: 'beginner',
    instructions: [
      'Colócate en posición de plancha con los antebrazos en el suelo',
      'Mantén el cuerpo en línea recta',
      'Contrae los abdominales',
      'Mantén la posición durante el tiempo indicado'
    ]
  }
]

export const mockWorkouts: Workout[] = [
  {
    id: '1',
    name: 'Entrenamiento de Fuerza - Piernas',
    description: 'Rutina enfocada en desarrollar fuerza en las piernas',
    exercises: [
      { id: '1', exerciseId: '1', reps: 12, weight: 0, restTime: 60, completed: false },
      { id: '2', exerciseId: '3', reps: 8, weight: 60, restTime: 90, completed: false },
      { id: '3', exerciseId: '5', reps: 1, weight: 0, restTime: 45, completed: false }
    ],
    estimatedDuration: 45,
    difficulty: 'intermediate',
    category: 'strength'
  },
  {
    id: '2',
    name: 'Entrenamiento de Fuerza - Tren Superior',
    description: 'Rutina para desarrollar fuerza en pecho, espalda y brazos',
    exercises: [
      { id: '4', exerciseId: '2', reps: 10, weight: 40, restTime: 90, completed: false },
      { id: '5', exerciseId: '4', reps: 15, weight: 0, restTime: 60, completed: false },
      { id: '6', exerciseId: '5', reps: 1, weight: 0, restTime: 45, completed: false }
    ],
    estimatedDuration: 40,
    difficulty: 'intermediate',
    category: 'strength'
  },
  {
    id: '3',
    name: 'Entrenamiento Funcional',
    description: 'Rutina completa para mejorar la condición física general',
    exercises: [
      { id: '7', exerciseId: '1', reps: 15, weight: 0, restTime: 30, completed: false },
      { id: '8', exerciseId: '4', reps: 12, weight: 0, restTime: 30, completed: false },
      { id: '9', exerciseId: '5', reps: 1, weight: 0, restTime: 30, completed: false }
    ],
    estimatedDuration: 30,
    difficulty: 'beginner',
    category: 'mixed'
  }
]

export const mockRoutines: Routine[] = [
  {
    id: '1',
    name: 'Rutina Principiante - 4 Semanas',
    description: 'Programa de entrenamiento para principiantes que quieren empezar su viaje fitness',
    workouts: [mockWorkouts[2], mockWorkouts[0]],
    frequency: 'weekly',
    daysPerWeek: 3,
    duration: 4,
    scheduledDays: ['monday', 'wednesday', 'friday']
  },
  {
    id: '2',
    name: 'Rutina Intermedia - 8 Semanas',
    description: 'Programa de entrenamiento para personas con experiencia que buscan mejorar su fuerza',
    workouts: [mockWorkouts[0], mockWorkouts[1]],
    frequency: 'weekly',
    daysPerWeek: 4,
    duration: 8,
    scheduledDays: ['tuesday', 'thursday', 'saturday', 'sunday']
  },
  {
    id: '3',
    name: 'Rutina Avanzada - 12 Semanas',
    description: 'Programa intensivo para atletas experimentados que buscan maximizar su rendimiento',
    workouts: [mockWorkouts[0], mockWorkouts[1], mockWorkouts[2]],
    frequency: 'weekly',
    daysPerWeek: 5,
    duration: 12,
    scheduledDays: ['monday', 'tuesday', 'wednesday', 'friday', 'saturday']
  }
]

export const mockGoals: Goal[] = [
  {
    id: '1',
    clientId: '1',
    title: 'Perder 5kg',
    description: 'Reducir peso corporal de forma saludable',
    targetValue: 60,
    currentValue: 65,
    unit: 'kg',
    deadline: new Date('2024-06-01'),
    isCompleted: false,
    category: 'weight'
  },
  {
    id: '2',
    clientId: '2',
    title: 'Aumentar Press de Banca',
    description: 'Mejorar la fuerza en press de banca',
    targetValue: 100,
    currentValue: 80,
    unit: 'kg',
    deadline: new Date('2024-08-01'),
    isCompleted: false,
    category: 'strength'
  },
  {
    id: '3',
    clientId: '3',
    title: 'Mantener Peso Actual',
    description: 'Mantener el peso corporal en 58kg',
    targetValue: 58,
    currentValue: 58,
    unit: 'kg',
    deadline: new Date('2024-12-01'),
    isCompleted: true,
    category: 'weight'
  }
]

export const mockProgressMetrics: ProgressMetrics[] = [
  {
    clientId: '1',
    date: new Date('2024-01-15'),
    weight: 65,
    bodyFat: 25,
    muscleMass: 45,
    measurements: {
      chest: 85,
      waist: 70,
      biceps: 28,
      forearms: 25,
      thighs: 55,
      calves: 35,
      neck: 35,
      shoulders: 95,
      hips: 90
    }
  },
  {
    clientId: '1',
    date: new Date('2024-02-15'),
    weight: 63,
    bodyFat: 23,
    muscleMass: 46,
    measurements: {
      chest: 84,
      waist: 68,
      biceps: 29,
      forearms: 26,
      thighs: 56,
      calves: 36,
      neck: 35,
      shoulders: 96,
      hips: 88
    }
  },
  {
    clientId: '2',
    date: new Date('2024-02-01'),
    weight: 80,
    bodyFat: 18,
    muscleMass: 62,
    measurements: {
      chest: 105,
      waist: 85,
      biceps: 35,
      forearms: 32,
      thighs: 65,
      calves: 40,
      neck: 40,
      shoulders: 115,
      hips: 100
    }
  },
  {
    clientId: '2',
    date: new Date('2024-03-01'),
    weight: 82,
    bodyFat: 17,
    muscleMass: 64,
    measurements: {
      chest: 107,
      waist: 84,
      biceps: 36,
      forearms: 33,
      thighs: 66,
      calves: 41,
      neck: 40,
      shoulders: 117,
      hips: 99
    }
  },
  {
    clientId: '3',
    date: new Date('2024-01-20'),
    weight: 58,
    bodyFat: 22,
    muscleMass: 42,
    measurements: {
      chest: 80,
      waist: 65,
      biceps: 25,
      forearms: 22,
      thighs: 50,
      calves: 32,
      neck: 32,
      shoulders: 88,
      hips: 85
    }
  },
  {
    clientId: '3',
    date: new Date('2024-02-20'),
    weight: 58,
    bodyFat: 21,
    muscleMass: 43,
    measurements: {
      chest: 81,
      waist: 64,
      biceps: 26,
      forearms: 23,
      thighs: 51,
      calves: 33,
      neck: 32,
      shoulders: 89,
      hips: 84
    }
  }
] 