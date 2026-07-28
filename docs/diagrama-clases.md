# Diagrama de Clases — Gym Now

Documentación visual de las entidades del dominio definidas en `gym/models.py`, representada con diagramas Mermaid (`flowchart`).

## Resumen de entidades

| Entidad | Descripción |
|---|---|
| `User` | Usuario base de Django (`auth.User`) |
| `CustomUser` | Perfil de rol asociado a un `User` |
| `Client` | Cliente del gimnasio (perfil de negocio) |
| `Exercise` | Ejercicio individual del catálogo |
| `Workout` | Entrenamiento compuesto por sets |
| `WorkoutSet` | Serie de un ejercicio dentro de un workout |
| `Routine` | Rutina que agrupa workouts |
| `ClientRoutine` | Asignación de rutina a un cliente |
| `RoutineProgress` | Registro de progreso de un workout en una asignación |
| `ProgressMetrics` | Métricas corporales del cliente |
| `Goal` | Objetivo personal del cliente |

---

## 1. Vista general de relaciones

```mermaid
flowchart TB
    User["User<br/>Django auth"]
    CustomUser["CustomUser"]
    Client["Client"]
    Exercise["Exercise"]
    Workout["Workout"]
    WorkoutSet["WorkoutSet"]
    Routine["Routine"]
    ClientRoutine["ClientRoutine"]
    RoutineProgress["RoutineProgress"]
    ProgressMetrics["ProgressMetrics"]
    Goal["Goal"]

    User -->|"1 — 1"| CustomUser
    User -->|"1 — 0..1"| Client

    Client -->|"1 — *"| ClientRoutine
    Client -->|"1 — *"| ProgressMetrics
    Client -->|"1 — *"| Goal

    Routine -->|"1 — *"| ClientRoutine
    Routine -->|"* — *"| Workout

    Workout -->|"1 — *"| WorkoutSet
    Exercise -->|"1 — *"| WorkoutSet

    ClientRoutine -->|"1 — *"| RoutineProgress
    Workout -->|"1 — *"| RoutineProgress
```

---

## 2. Dominio de usuarios y clientes

```mermaid
flowchart LR
    subgraph AUTH["Autenticación"]
        User["User<br/>─────────────<br/>+ id<br/>+ username<br/>+ email<br/>+ password<br/>+ first_name<br/>+ last_name<br/>+ date_joined<br/>+ last_login"]
    end

    subgraph PROFILE["Perfiles"]
        CustomUser["CustomUser<br/>─────────────<br/>+ id<br/>+ role<br/>  client | trainer<br/>  guest | owner"]
        Client["Client<br/>─────────────<br/>+ id<br/>+ name<br/>+ email<br/>+ phone<br/>+ birth_date<br/>+ weight<br/>+ height<br/>+ goals JSON<br/>+ join_date<br/>+ profile_image<br/>+ subscription_type<br/>+ subscription_start<br/>+ subscription_end<br/>+ notes<br/>+ emergency_contact<br/>+ medical_conditions<br/>─────────────<br/>+ age property<br/>+ assigned_routines"]
    end

    User -->|"OneToOne<br/>related_name: custom_profile"| CustomUser
    User -->|"OneToOne<br/>related_name: client_profile<br/>nullable"| Client
```

---

## 3. Dominio de entrenamiento

```mermaid
flowchart TB
    Exercise["Exercise<br/>─────────────<br/>+ id<br/>+ name<br/>+ description<br/>+ muscle_groups JSON<br/>+ equipment JSON<br/>+ difficulty<br/>  beginner | intermediate | advanced<br/>+ instructions JSON<br/>+ video_url<br/>+ image_url"]

    Workout["Workout<br/>─────────────<br/>+ id<br/>+ name<br/>+ description<br/>+ estimated_duration<br/>+ difficulty<br/>  beginner | intermediate | advanced<br/>+ category<br/>  strength | cardio<br/>  flexibility | mixed"]

    WorkoutSet["WorkoutSet<br/>─────────────<br/>+ id<br/>+ reps<br/>+ weight<br/>+ rest_time<br/>+ completed"]

    Routine["Routine<br/>─────────────<br/>+ id<br/>+ name<br/>+ description<br/>+ frequency<br/>  daily | weekly | custom<br/>+ days_per_week<br/>+ duration weeks<br/>+ scheduled_days JSON"]

    Workout -->|"1 — *<br/>FK related_name: sets"| WorkoutSet
    Exercise -->|"1 — *<br/>FK"| WorkoutSet
    Routine -->|"* — *<br/>M2M related_name: routines"| Workout
```

---

## 4. Dominio de asignación y progreso

```mermaid
flowchart TB
    Client["Client"]
    Routine["Routine"]
    Workout["Workout"]

    ClientRoutine["ClientRoutine<br/>─────────────<br/>+ id<br/>+ start_date<br/>+ end_date<br/>+ is_active<br/>+ assigned_days JSON"]

    RoutineProgress["RoutineProgress<br/>─────────────<br/>+ id<br/>+ completed_at<br/>+ notes<br/>+ rating"]

    ProgressMetrics["ProgressMetrics<br/>─────────────<br/>+ id<br/>+ date<br/>+ weight<br/>+ body_fat<br/>+ muscle_mass<br/>+ measurements JSON<br/>+ photos JSON"]

    Goal["Goal<br/>─────────────<br/>+ id<br/>+ title<br/>+ description<br/>+ target_value<br/>+ current_value<br/>+ unit<br/>+ deadline<br/>+ is_completed<br/>+ category<br/>  weight | strength<br/>  endurance | flexibility | custom"]

    Client -->|"1 — *<br/>related_name: client_routines"| ClientRoutine
    Routine -->|"1 — *"| ClientRoutine

    ClientRoutine -->|"1 — *"| RoutineProgress
    Workout -->|"1 — *"| RoutineProgress

    Client -->|"1 — *"| ProgressMetrics
    Client -->|"1 — *"| Goal
```

---

## 5. Flujo de composición de una rutina

Desde el catálogo hasta la ejecución por el cliente:

```mermaid
flowchart LR
    Exercise["Exercise"] --> WorkoutSet["WorkoutSet"]
    WorkoutSet --> Workout["Workout"]
    Workout --> Routine["Routine"]
    Routine --> ClientRoutine["ClientRoutine"]
    Client["Client"] --> ClientRoutine
    ClientRoutine --> RoutineProgress["RoutineProgress"]
    Workout --> RoutineProgress
```

---

## Cardinalidades

| Relación | Tipo | Cardinalidad |
|---|---|---|
| `User` → `CustomUser` | OneToOne | 1 — 1 |
| `User` → `Client` | OneToOne (nullable) | 1 — 0..1 |
| `Client` → `ClientRoutine` | ForeignKey | 1 — * |
| `Routine` → `ClientRoutine` | ForeignKey | 1 — * |
| `Routine` ↔ `Workout` | ManyToMany | * — * |
| `Workout` → `WorkoutSet` | ForeignKey | 1 — * |
| `Exercise` → `WorkoutSet` | ForeignKey | 1 — * |
| `ClientRoutine` → `RoutineProgress` | ForeignKey | 1 — * |
| `Workout` → `RoutineProgress` | ForeignKey | 1 — * |
| `Client` → `ProgressMetrics` | ForeignKey | 1 — * |
| `Client` → `Goal` | ForeignKey | 1 — * |

---

## Notas

- `CustomUser` se crea automáticamente al guardar un `User` (signal `post_save`).
- Al crear un `Client` sin usuario asociado, se genera un `User` con username = email y contraseña por defecto basada en la edad (`{edad}00`).
- `Client.goals` es un JSON de textos libres; la entidad `Goal` modela objetivos estructurados con progreso medible.
- `Client.assigned_routines` es una property que expone las rutinas activas vía `ClientRoutine`.
