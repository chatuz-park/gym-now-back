# Diagrama Entidad-Relación (ER) — Gym Now

Modelo relacional de las entidades definidas en `gym/models.py`, representado con diagramas Mermaid (`erDiagram`).

## Resumen

El esquema cubre tres áreas:

1. **Usuarios y clientes** — autenticación Django y perfiles de negocio
2. **Catálogo de entrenamiento** — ejercicios, workouts, sets y rutinas
3. **Asignación y seguimiento** — rutinas del cliente, progreso, métricas y objetivos

---

## 1. Diagrama ER completo

```mermaid
erDiagram
    User ||--|| CustomUser : tiene_perfil
    User ||--o| Client : puede_ser
    Client ||--o{ ClientRoutine : tiene_asignadas
    Routine ||--o{ ClientRoutine : asignada_a
    Routine }o--o{ Workout : incluye
    Workout ||--o{ WorkoutSet : compuesto_por
    Exercise ||--o{ WorkoutSet : usado_en
    ClientRoutine ||--o{ RoutineProgress : registra
    Workout ||--o{ RoutineProgress : completado_en
    Client ||--o{ ProgressMetrics : mide
    Client ||--o{ Goal : define

    User {
        int id PK
        string username UK
        string email
        string password
        string first_name
        string last_name
        datetime date_joined
        datetime last_login
    }

    CustomUser {
        int id PK
        int user_id FK
        string role
    }

    Client {
        int id PK
        int user_id FK
        string name
        string email UK
        string phone
        date birth_date
        float weight
        float height
        json goals
        date join_date
        string profile_image
        string subscription_type
        date subscription_start
        date subscription_end
        text notes
        string emergency_contact
        string medical_conditions
    }

    Exercise {
        int id PK
        string name
        text description
        json muscle_groups
        json equipment
        string difficulty
        json instructions
        string video_url
        string image_url
    }

    Workout {
        int id PK
        string name
        text description
        int estimated_duration
        string difficulty
        string category
    }

    WorkoutSet {
        int id PK
        int workout_id FK
        int exercise_id FK
        int reps
        float weight
        int rest_time
        boolean completed
    }

    Routine {
        int id PK
        string name
        text description
        string frequency
        int days_per_week
        int duration
        json scheduled_days
    }

    ClientRoutine {
        int id PK
        int client_id FK
        int routine_id FK
        date start_date
        date end_date
        boolean is_active
        json assigned_days
    }

    RoutineProgress {
        int id PK
        int client_routine_id FK
        int workout_id FK
        datetime completed_at
        text notes
        int rating
    }

    ProgressMetrics {
        int id PK
        int client_id FK
        date date
        float weight
        float body_fat
        float muscle_mass
        json measurements
        json photos
    }

    Goal {
        int id PK
        int client_id FK
        string title
        text description
        float target_value
        float current_value
        string unit
        date deadline
        boolean is_completed
        string category
    }
```

---

## 2. Dominio de usuarios y clientes

```mermaid
erDiagram
    User ||--|| CustomUser : uno_a_uno
    User ||--o| Client : uno_a_cero_o_uno

    User {
        int id PK
        string username UK
        string email
        string password
        string first_name
        string last_name
    }

    CustomUser {
        int id PK
        int user_id FK
        string role
    }

    Client {
        int id PK
        int user_id FK
        string name
        string email UK
        string phone
        date birth_date
        float weight
        float height
        string subscription_type
        date subscription_start
        date subscription_end
    }
```

`CustomUser.user_id` y `Client.user_id` son Unique (OneToOne). `Client.user_id` puede ser null.

---

## 3. Dominio de entrenamiento

```mermaid
erDiagram
    Routine }o--o{ Workout : muchos_a_muchos
    Workout ||--o{ WorkoutSet : uno_a_muchos
    Exercise ||--o{ WorkoutSet : uno_a_muchos

    Exercise {
        int id PK
        string name
        text description
        json muscle_groups
        json equipment
        string difficulty
        json instructions
        string video_url
        string image_url
    }

    Workout {
        int id PK
        string name
        text description
        int estimated_duration
        string difficulty
        string category
    }

    WorkoutSet {
        int id PK
        int workout_id FK
        int exercise_id FK
        int reps
        float weight
        int rest_time
        boolean completed
    }

    Routine {
        int id PK
        string name
        text description
        string frequency
        int days_per_week
        int duration
        json scheduled_days
    }
```

> La relación M:N entre `Routine` y `Workout` se materializa en Django como tabla intermedia automática (`routine_workouts`).

---

## 4. Dominio de asignación y seguimiento

```mermaid
erDiagram
    Client ||--o{ ClientRoutine : uno_a_muchos
    Routine ||--o{ ClientRoutine : uno_a_muchos
    ClientRoutine ||--o{ RoutineProgress : uno_a_muchos
    Workout ||--o{ RoutineProgress : uno_a_muchos
    Client ||--o{ ProgressMetrics : uno_a_muchos
    Client ||--o{ Goal : uno_a_muchos

    Client {
        int id PK
        string name
        string email UK
    }

    Routine {
        int id PK
        string name
    }

    Workout {
        int id PK
        string name
    }

    ClientRoutine {
        int id PK
        int client_id FK
        int routine_id FK
        date start_date
        date end_date
        boolean is_active
        json assigned_days
    }

    RoutineProgress {
        int id PK
        int client_routine_id FK
        int workout_id FK
        datetime completed_at
        text notes
        int rating
    }

    ProgressMetrics {
        int id PK
        int client_id FK
        date date
        float weight
        float body_fat
        float muscle_mass
        json measurements
        json photos
    }

    Goal {
        int id PK
        int client_id FK
        string title
        float target_value
        float current_value
        string unit
        date deadline
        boolean is_completed
        string category
    }
```

---

## 5. Diccionario de relaciones

| Entidad origen | Entidad destino | Cardinalidad | Tipo / implementación | On delete |
|---|---|---|---|---|
| `User` | `CustomUser` | 1:1 | OneToOne (`user_id` UK) | CASCADE |
| `User` | `Client` | 1:0..1 | OneToOne nullable (`user_id` UK) | CASCADE |
| `Client` | `ClientRoutine` | 1:N | ForeignKey | CASCADE |
| `Routine` | `ClientRoutine` | 1:N | ForeignKey | CASCADE |
| `Routine` | `Workout` | M:N | ManyToMany | — |
| `Workout` | `WorkoutSet` | 1:N | ForeignKey | CASCADE |
| `Exercise` | `WorkoutSet` | 1:N | ForeignKey | CASCADE |
| `ClientRoutine` | `RoutineProgress` | 1:N | ForeignKey | CASCADE |
| `Workout` | `RoutineProgress` | 1:N | ForeignKey | CASCADE |
| `Client` | `ProgressMetrics` | 1:N | ForeignKey | CASCADE |
| `Client` | `Goal` | 1:N | ForeignKey | CASCADE |

---

## 6. Claves y restricciones

| Tabla | PK | UK / índices lógicos | Notas |
|---|---|---|---|
| `User` | `id` | `username` | Modelo Django `auth_user` |
| `CustomUser` | `id` | `user_id` | Rol del usuario |
| `Client` | `id` | `email`, `user_id` | `phone` validado como único en `clean()` |
| `Exercise` | `id` | — | Catálogo global |
| `Workout` | `id` | — | Contenedor de sets |
| `WorkoutSet` | `id` | — | Une workout + exercise |
| `Routine` | `id` | — | Agrupa workouts |
| `ClientRoutine` | `id` | — | Asignación cliente ↔ rutina |
| `RoutineProgress` | `id` | — | Historial de ejecución |
| `ProgressMetrics` | `id` | — | Snapshot corporal por fecha |
| `Goal` | `id` | — | Objetivo medible del cliente |

---

## 7. Campos enumerados (choices)

| Entidad | Campo | Valores |
|---|---|---|
| `CustomUser` | `role` | `client`, `trainer`, `guest`, `owner` |
| `Client` | `subscription_type` | `standard`, `premium`, `personalized` |
| `Exercise` | `difficulty` | `beginner`, `intermediate`, `advanced` |
| `Workout` | `difficulty` | `beginner`, `intermediate`, `advanced` |
| `Workout` | `category` | `strength`, `cardio`, `flexibility`, `mixed` |
| `Routine` | `frequency` | `daily`, `weekly`, `custom` |
| `Goal` | `category` | `weight`, `strength`, `endurance`, `flexibility`, `custom` |

---

## Notas de modelado

- Todas las FKs usan `on_delete=CASCADE`: al eliminar el padre se eliminan los registros dependientes.
- `Client.user` es opcional; si se crea un cliente sin usuario, un signal crea el `User` automáticamente.
- `Client.goals` (JSON de textos) y la entidad `Goal` coexisten: el primero es lista libre; el segundo es seguimiento estructurado.
- Campos `JSONField` (`muscle_groups`, `equipment`, `instructions`, `scheduled_days`, `assigned_days`, `measurements`, `photos`) no se normalizan en tablas hijas.
