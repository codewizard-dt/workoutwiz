# Legacy Fitness Tracker (Node.js/Express/Mongoose/React)

A comprehensive inventory of the legacy workout tracking system that will be selectively ported to the modern multi-agent architecture.

---

## Overview

**Tech Stack**: Node.js + Express | MongoDB + Mongoose | React 17 (CRA) + Redux | Semantic UI

**Purpose**: Self-directed gym users log workouts, search exercises, and receive coaching guidance through a unified web interface.

**Code Structure**: 
- Backend: `/src/` — Express routers, Mongoose schemas, middleware, database utilities
- Frontend: `/client/src/` — React components, Redux store, API client, semantic UI styling

---

## Backend (Express + MongoDB)

### Server Entry Point (`src/server.ts`)

- Express app initialization with middleware (body-parser, cookie-parser, CORS)
- MongoDB Atlas connection with configurable env-based credentials
- Three main routers mounted: `/auth`, `/exercises`, `/workouts`
- Static file serving (`build/public/`, `/images`)
- Fallback 404 handler redirects all unknown routes to `/` (SPA support)
- Server starts on configurable `PORT` (default 8080) with retry logic

### Authentication Router (`src/routers/AuthRouter.ts`)

**Endpoints**:
- `POST /auth/register` — Create user account
  - Validates password confirmation
  - Returns error if email already exists
  - Returns JWT access token on success
  - Password hashed via bcrypt in User schema pre-save hook
- `POST /auth/signin` — Authenticate and create session
  - Validates email + password via `User.findAndValidate()`
  - Sets signed auth cookie on success
  - Returns user ID and email
- `GET /auth/signout` — Revoke auth cookie
- `GET /auth/getToken` — Verify existing token
  - Checks X-ACCESS-TOKEN header or signed cookie
  - Returns user info if valid

**Auth Middleware** (`src/middleware/JsonWebToken.ts`):
- JWT generation with user ID and email
- Token verification and validation
- Cookie signing/revocation with HMAC secret
- `jwtRequireAuth` middleware — gates all `/exercises` and `/workouts` routes

### User Schema (`src/schemas/User.ts`)

**Fields**:
- `email` (String, required) — Unique identifier
- `password` (String, required) — Bcrypt-hashed
- `timestamps` — createdAt, updatedAt auto-managed

**Statics**:
- `findAndValidate(email, password)` — Authenticate user, return user object or false

**Instance Methods**:
- `serialize()` — Return public user fields

### Exercise Router (`src/routers/ExerciseRouter.ts`)

**Endpoints**:
- `POST /exercises/` — Bulk insert exercises
  - Accepts single exercise or array (split into 100-item chunks for Mongoose)
  - Typically called once at startup to load exercises.json
- `GET /exercises/` — Fetch all exercises (no filtering, returns full list)
- `POST /exercises/search` — Search by criteria
  - Query params: `name`, `bodyPart`, `equipment`, `target` (all optional)
  - Name search: regex-based with word boundary matching (e.g., "bench press" → `(?=.*\bBench)(?=.*Press)`)
  - Returns sorted by name

### Exercise Schema (`src/schemas/Exercise.ts`)

**Fields**:
- `name` (String, required) — Exercise name (e.g., "Barbell Flat Bench Press")
- `bodyPart` (String, required) — Primary body part (e.g., "chest")
- `target` (String, required) — Target muscle (e.g., "pectorals")
- `equipment` (String, required) — Equipment needed (e.g., "barbell")
- `gifUrl` (String, required) — URL to animated exercise GIF

**Statics**:
- `getFindQuery(params)` — Build Mongoose query object with regex support for name fuzzy-matching

**Instance Methods**:
- `serialize()` — Return public exercise fields

**Sample Data** (from legacy exercises.json):
```
BodyPart: ["any", "back", "cardio", "chest", "lower arms", "lower legs", "neck", "shoulders", "upper arms", "upper legs", "waist"]
Target: ["any", "abductors", "abs", "adductors", "biceps", "calves", "cardiovascular system", "delts", "forearms", "glutes", "hamstrings", "lats", "levator scapulae", "pectorals", "quads", "serratus anterior", "spine", "traps", "triceps", "upper back"]
Equipment: ["any", "assisted", "band", "barbell", "body weight", "bosu ball", "cable", "dumbbell", "elliptical machine", "ez barbell", "hammer", "kettlebell", "leverage machine", "medicine ball", "olympic barbell", "resistance band", "roller", "rope", "skierg machine", "sled machine", "smith machine", "stability ball", "stationary bike", "stepmill machine", "tire", "trap bar", "upper body ergometer", "weighted", "wheel roller"]
~50 exercises total covering all combinations
```

### Workout Router (`src/routers/WorkoutRouter.ts`)

**Endpoints**:
- `GET /workouts/user/:userId` — Fetch all workouts for user
  - Requires JWT + userId match (middleware `jwtUserMatch`)
  - Populates exercise references recursively
  - Sorted by datetime descending (most recent first)
  - Returns serialized workout objects
- `POST /workouts/user/:userId` — Create or update workout
  - If `_id` present: update (find and replace datetime + sequenceList)
  - If no `_id`: create new (returns generated ID)
  - Associates workout with user ID
- `GET /workouts/:workoutId` — Fetch single workout details
  - No user validation (potential security concern?)
- `DELETE /workouts/:workoutId` — Delete workout
  - Requires user ID match

### Workout Schema (`src/schemas/Workout.ts`)

**Fields**:
- `datetime.start` (Number) — Unix timestamp when workout began
- `datetime.end` (Number) — Unix timestamp when workout ended
- `sequenceList` (Array of SequenceItem arrays) — Grouped sequences/sets
  - Outer array: phases (warmup, main, cooldown)
  - Inner array: individual sets/intervals
- `user` (ObjectId ref → User) — Workout owner

**Statics**:
- `findAndPopulate(params)` — Find workout(s) and recursively populate exercise references

**Instance Methods**:
- `serialize()` — Return public fields

### WorkoutSequence Schema (`src/schemas/WorkoutSequence.ts`)

**SequenceItem** (no `_id` at item level):
- `exercise` (ObjectId ref → Exercise) — Which exercise was performed
- `reps` (Number) — Repetitions (for strength sets)
- `weight` (Number) — Weight lifted (lbs or kg)
- `barWeight` (Number) — Just the bar weight (for calculated 1RM)
- `weightAssist` (Number) — Assisted weight (machines)
- `duration` (Number) — Duration in seconds (cardio/intervals)
- `speed` (Number) — Speed (e.g., mph for running)
- `distance` (Number) — Distance covered (miles, km)
- `incline` (Number) — Treadmill/rower incline
- `verticalRise` (Number) — Elevation gain
- `calories` (Number) — Calories burned (estimated from machine)

**Notes**:
- A single SequenceItem can be both a set (reps + weight) AND an interval (duration + speed), model allows flexibility
- Nested in Workout.sequenceList as `[[SequenceItem], [SequenceItem], ...]` to group by phase
- No explicit "rest period" field; duration could represent rest if context is clear

### Middleware

**ErrorHandler** (`src/middleware/ErrorHandler.ts`): 
- Express error-handling middleware (details not shown, but exists)

**MongooseErrors** (`src/middleware/MongooseErrors.ts`): 
- Likely catches and formats Mongoose validation/connection errors

### Utilities

**asyncCatch** (`src/utils/asyncCatch.ts`):
- Wrapper to catch async route handler errors and pass to Express error handler

---

## Frontend (React + Redux)

### App Structure

**Entry**: `src/App.tsx` — React Router with two route trees:
1. **Guest routes** (`/`, `/signin`, `/register`) — GuestOnly guard
2. **Authenticated routes** (`/dashboard`, `/dashboard/workout`, `/dashboard/workout/new`) — AuthGuard

**Global Layout**: NavBar + Container, AuthProvider wraps everything

### Authentication Context & Guards

**AuthProvider** (`src/components/auth/AuthProvider.tsx`):
- Manages auth state (user ID, email, JWT token)
- Syncs with backend on mount (`GET /auth/getToken`)
- Provides auth context to all child components

**AuthGuard** & **GuestOnly**:
- Route-level guards to redirect unauthenticated users or already-logged-in users

**AuthContext** (`src/components/auth/AuthContext.tsx`):
- Defines shape of auth state, login/logout functions

### Redux Store

**Root State**: `RootState` combines `auth`, `exercises`, `workouts` slices

#### Auth Slice (`redux/reducers/Auth.ts`)
- State: `{ userId, email, token }`
- Actions: set user, clear on logout

#### Exercise Slice (`redux/reducers/Exercise.ts`)
- State: 
  - `list` — all exercises loaded from server
  - `current` — selected exercise for building workouts
  - `search` — current search query (name, bodyPart, equipment, target)
- Actions: load list, update search params, set current, clear search

#### Workout Slice (`redux/reducers/Workout.ts`)
- State:
  - `list` — user's saved workouts
  - `current` — workout being built (sequenceList, datetime)
  - `isSearching` — flag for exercise picker visibility
- Actions: load user workouts, save workout, delete workout, select/update current, add sets to sequence

### Redux Actions & Thunks

**exercise.ts**:
- `loadExercises()` — Thunk to fetch all exercises from GET `/exercises/`
- `searchExercises(criteria)` — Thunk to POST to `/exercises/search`
- `setName`, `setBodyPart`, `setEquipment`, `setTarget` — Update search UI state

**workout.ts**:
- `loadUserWorkouts()` — Thunk to fetch workouts from GET `/workouts/user/:userId`
- `saveWorkout(workout)` — Thunk to POST/PUT to `/workouts/user/:userId`
- `deleteWorkout(workoutId)` — Thunk to DELETE `/workouts/:workoutId`
- `selectWorkout(workout)` — Set current workout
- `addSetToSequence(sequenceItem)` — Add set/interval to current workout's sequenceList
- `closeSearch()` — Hide exercise picker overlay

### Data Models (TypeScript Interfaces)

**Exercise** (`src/models/Exercise.ts`):
```typescript
interface Exercise {
  _id: string
  name: string
  bodyPart: BodyPart
  target: TargetMuscle
  equipment: Equipment
  gifUrl: string
}

// Enums
type BodyPart = "any" | "back" | "chest" | "shoulders" | ...
type TargetMuscle = "any" | "abs" | "biceps" | "pectorals" | ...
type Equipment = "any" | "barbell" | "dumbbell" | "bodyweight" | ...
```

**Workout** (`src/models/Workout.ts`):
```typescript
interface Workout {
  _id?: string
  user?: string
  datetime: {
    start?: number
    end?: number
  }
  sequenceList: WorkoutSequenceList
}

interface WorkoutSet extends BasicInfo {
  reps: number
}
interface WorkoutInterval extends BasicInfo {
  duration: number
  speed?: number
  distance?: number
  incline?: number
  verticalRise?: number
  calories?: number
}
type WorkoutSequence = (WorkoutSet & WorkoutInterval)[]
type WorkoutSequenceList = WorkoutSequence[]

interface BasicInfo {
  exercise: Exercise
  weight?: number
  weightAssist?: number
  barWeight?: number
}
```

### Component Hierarchy

**Auth Components**:
- `Login.tsx` — Email/password form, calls Redux thunk on submit
- `Register.tsx` — Registration form with password confirmation
- `GuestOnly.tsx`, `AuthGuard.tsx` — Route guards

**Dashboard** (`Dashboard.tsx`):
- Main authenticated view
- Shows user's workout list as cards
- Links to `/dashboard/workout/new` or `/dashboard/workout/:id`

**Workout Components**:
- `NewWorkout.tsx` — Initializes empty workout, navigates to CurrentWorkout
- `CurrentWorkout.tsx` — Main workout builder UI
  - Shows current phase (warmup, main, cooldown)
  - Displays exercise picker overlay
  - Lists sets/intervals for current phase
  - Add/edit/delete set controls
- `ShowWorkout.tsx` — Read-only view of past workout
- `CurrentSet.tsx`, `CurrentInterval.tsx` — Form inputs for reps/weight or duration/distance
- `CurrentSequenceItem.tsx` — Single set/interval builder
- `WorkoutDatetime.tsx` — Start/end time picker
- `WorkoutListCard.tsx` — Card component for list view

**Exercise Components**:
- `ExerciseSearch.tsx` — Search form (name, bodyPart, target, equipment filters)
- `SearchResults.tsx` — Tabbed results or modal
- `ExerciseListItem.tsx` — Clickable exercise row
- `ExerciseCard.tsx` — Larger card view
- `ExerciseImage.tsx` — GIF display
- `SearchResultHeader.tsx`, `SearchByName.tsx`, `ExerciseSearchDetails.tsx` — Search sub-components

**Utility Components**:
- `ChunkCardList.tsx`, `ChunkList.tsx` — List rendering (chunked for performance)
- `ConfirmDelete.tsx`, `ConfirmEdit.tsx`, `ConfirmCopy.tsx`, `ConfirmButton.tsx` — Confirmation modals
- `AppDateTime.ts`, `AppExponentialChange.ts`, `HasStatistics.ts` — Utility classes
- `StatLabels.tsx`, `FadingMessage.tsx` — Display helpers
- `AppIconButton.tsx`, `AppNumber.tsx`, `AppDropdown.tsx` — Form controls
- `AppPlaceholderImage.tsx` — Fallback for missing exercise GIFs

**Navigation**:
- `NavBar.tsx` — Header with logo, links
- `ChunkNavBar.tsx` — Sub-navigation for workout phases
- `NavLink.tsx`, `ButtonLink.tsx` — Router-aware link components
- `BackButton.tsx`, `ForwardButton.tsx` — Navigation controls
- `NotFound.tsx` — 404 page

### API Client

**API Utils** (`src/api/util/AppAxios.ts`):
- Axios instance with default base URL (`http://localhost:8080` via proxy)
- Handles JWT token in headers

**ExerciseDB.ts**:
- `getExercises()` — GET `/exercises/`
- `searchExercises(criteria)` — POST `/exercises/search`

**WorkoutDB.ts**:
- `getWorkouts(userId)` — GET `/workouts/user/:userId`
- `saveWorkout(workout)` — POST `/workouts/user/:userId`
- `deleteWorkout(workoutId)` — DELETE `/workouts/:workoutId`

**UserAuth.ts**:
- `register(email, password)` — POST `/auth/register`
- `signin(email, password)` — POST `/auth/signin`
- `signout()` — GET `/auth/signout`
- `getToken()` — GET `/auth/getToken`

### Styling

- **Semantic UI React** — Component library (buttons, forms, dropdowns, modals, segments)
- **Semantic CSS** — Bundled in `/src/semantic/` (~250+ CSS files, pre-compiled)
- **SASS** — Custom styles in `.sass` files (e.g., `Search.sass`, `ChunkNavBar.sass`, `App.sass`)

### State Flow Example: Create Workout

1. User clicks "New Workout" button
2. `NewWorkout` component dispatches `selectWorkout({ datetime: { start: now }, sequenceList: [[]] })`
3. Navigates to `/dashboard/workout`
4. `CurrentWorkout` renders, user sees empty phase list
5. User clicks "Add Exercise"
6. Exercise search modal opens, Redux state sets `isSearching: true`
7. User types and filters exercises, Redux updates search params
8. User clicks exercise → Redux sets `current: exercise` and closes search
9. User enters reps, weight → form updates Redux state
10. User clicks "Save Set" → Redux adds to `current.sequenceList[0]`
11. User clicks "Save Workout" → Redux thunk POSTs to backend, receives `_id`, updates Redux list

---

## Data Flow: Exercises.json → Database

**Setup** (one-time):
1. Get `exercises.json` (external file, ~50 exercises)
2. User runs setup script or admin endpoint
3. Script reads JSON, makes POST request to `/exercises/` with array
4. Express route batches into 100-item chunks, inserts into MongoDB
5. Frontend can now search/select exercises in workout builder

**No automatic refresh**: Exercises are static in this system (not updated from external source).

---

## Known Limitations & Gaps

- **No exercises.json in repo**: External data file, setup process unclear
- **No password reset**: User must re-register if password lost
- **No social features**: Solo tracking only
- **No image fallback**: Missing GIFs cause broken image
- **Fuzzy matching for exercise names**: Regex-based, not true fuzzy (e.g., "bench" finds "Barbell Bench" but not "Bench Barbell")
- **No workout templates**: Every workout must be built from scratch
- **No REST period tracking**: Duration field dual-purpose (cardio OR rest)
- **No nutrition logging**: Calories tracked per set, no macro breakdown
- **No goal tracking**: No targets or progress monitoring
- **Security concerns**: DELETE `/workouts/:workoutId` doesn't validate user ownership
- **Deprecated CRA**: React 17 + CRA is no longer recommended; Vite is modern standard

---

## Summary Table

| Aspect | Details |
|--------|---------|
| **Languages** | TypeScript (backend), TypeScript (frontend) |
| **Frameworks** | Express (backend), React 17 (frontend) |
| **Database** | MongoDB Atlas + Mongoose |
| **State** | Redux (frontend) |
| **Auth** | JWT + bcrypt |
| **API Style** | REST |
| **UI Library** | Semantic UI React |
| **Build Tool** | Create React App (webpack) |
| **Styling** | Semantic UI CSS + SASS |
| **Entry Points** | `src/server.ts` (backend), `src/index.tsx` (frontend) |
| **Deployed?** | Heroku support (env-based config) |
