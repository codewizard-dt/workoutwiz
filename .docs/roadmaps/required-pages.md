# Frontend Required Pages And Wireframes

## Scope

These wireframes define the minimal frontend needed to satisfy PRD 001. The UI should make the multi-agent behavior easy to assess: one chat surface, clear routing evidence, dataset traceability, and structured workout inspection.

## Route Tree

```txt
/
  -> /chat when authenticated
  -> /login when unauthenticated

/login
/register

/chat
/workouts
/workouts/new
/workouts/:workoutId
/exercises
```

All routes except `/login`, `/register`, and optionally `/exercises` should require authentication.

## Shared App Shell

```txt
┌──────────────────────────────────────────────────────────────────────────────┐
│ Workout Wiz          Chat   Workouts   Exercises   [Start New Workout] Logout│
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Page content                                                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Required behavior:

- Primary navigation highlights the active page.
- `Start New Workout` is always available to authenticated users and links to `/workouts/new`.
- `Logout` is always available to authenticated users.
- Logout returns the user to `/login`.
- Mobile layout collapses navigation into a compact top row or menu.

## Login Page

```txt
┌────────────────────────────────────────┐
│ Workout Wiz                            │
│ Sign in                                │
│                                        │
│ Email                                  │
│ ┌────────────────────────────────────┐ │
│ │                                    │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Password                               │
│ ┌────────────────────────────────────┐ │
│ │                                    │ │
│ └────────────────────────────────────┘ │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Sign in                            │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Need an account? Register              │
└────────────────────────────────────────┘
```

States:

- Loading: disable submit and show `Signing in...`.
- Error: show one concise inline error above the form.
- Success: redirect to `/chat`.

## Register Page

```txt
┌────────────────────────────────────────┐
│ Workout Wiz                            │
│ Create account                         │
│                                        │
│ Email                                  │
│ ┌────────────────────────────────────┐ │
│ │                                    │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Password                               │
│ ┌────────────────────────────────────┐ │
│ │                                    │ │
│ └────────────────────────────────────┘ │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Create account                     │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Already have an account? Sign in       │
└────────────────────────────────────────┘
```

States:

- Loading: disable submit and show `Creating account...`.
- Error: show validation or API error inline.
- Success: set token if returned, otherwise redirect to `/login`.

## Chat Page

```txt
┌──────────────────────────────────────────────────────────────────────────────┐
│ Chat                                                                         │
│ Ask questions, generate workouts, or log completed activity.                 │
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────┐ ┌─────────────────────────┐ │
│ │ Prompt chips                                 │ │ Previous Workouts        │ │
│ │ [Deadlift muscles] [30 min dumbbell workout] │ │ ┌─────────────────────┐ │ │
│ │ [3x10 bench at 185] [Bench press]            │ │ │ Jun 6 Upper Body    │ │ │
│ ├──────────────────────────────────────────────┤ │ │ 3 phases • 12 sets  │ │ │
│ │ Conversation                                 │ │ │ [View Details]      │ │ │
│ │                                              │ │ └─────────────────────┘ │ │
│ │ You                                          │ │ ┌─────────────────────┐ │ │
│ │ What muscles does a deadlift work?           │ │ │ Jun 5 Log           │ │ │
│ │                                              │ │ │ 1 phase • 4 sets    │ │ │
│ │ Assistant      Route: COACH  Confidence: .94 │ │ │ [View Details]      │ │ │
│ │ Deadlifts primarily train...                 │ │ └─────────────────────┘ │ │
│ │                                              │ │                         │ │
│ │ ┌──────────────────────────────────────────┐ │ │ [All Workouts]          │ │
│ │ │ Routing details                         │ │ │                         │ │
│ │ │ router: COACH, confidence .94            │ │ │                         │ │
│ │ └──────────────────────────────────────────┘ │ │                         │ │
│ ├──────────────────────────────────────────────┤ │                         │ │
│ │ ┌──────────────────────────────────────────┐ │ │                         │ │
│ │ │ Message Morgan typed...                  │ │ │                         │ │
│ │ └──────────────────────────────────────────┘ │ │                         │ │
│ │                         [Send] [Clear]       │ │                         │ │
│ └──────────────────────────────────────────────┘ └─────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

Required behavior:

- Desktop layout is approximately two-thirds chat on the left and one-third previous workout cards on the right.
- Previous workout cards link to `/workouts/:workoutId`.
- Preserve `session_id` across messages in the current browser session.
- Display each assistant response as readable text.
- Display route and confidence when provided by `/api/chat/`.
- Show audit log details in a collapsible panel per response or session.
- Keep sample prompt chips available to speed up assessor testing.
- Empty input should not submit.
- API errors should render as user-facing messages, not blank states.
- Keep styling consistent with the rest of the app; avoid spending implementation time on decorative micro-details that do not clarify the workout/chat flow.

Minimum response rendering:

```txt
┌──────────────────────────────────────────────────────────────────────────────┐
│ Assistant                                                                    │
│ Route badge                                                                  │
│ Confidence value                                                             │
│ Reply text                                                                   │
│ Optional audit details                                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Workouts Page

```txt
┌──────────────────────────────────────────────────────────────────────────────┐
│ Workouts                                                        [New Workout]│
├──────────────────────────────────────────────────────────────────────────────┤
│ Date                       Phases             Sets              Actions      │
│ Jun 6, 2026 8:30 AM        3                  12                [View] [Del] │
│ Jun 5, 2026 6:15 PM        1                  4                 [View] [Del] │
└──────────────────────────────────────────────────────────────────────────────┘
```

Required behavior:

- Link each row to `/workouts/:workoutId`.
- Show empty state with a link to `/chat` and `/workouts/new`.
- Delete remains available but secondary to viewing.
- Loading and error states should be visible.

## Workout Details Page

```txt
┌──────────────────────────────────────────────────────────────────────────────┐
│ ← Workouts                                                                   │
│ Workout Details                                                [Replay All] │
│ Started: Jun 6, 2026 8:30 AM           Ended: Jun 6, 2026 9:04 AM           │
│ Enjoyment                                                                    │
│ Sad  ○──○──●──○──○  Happy                                                    │
│ Note                                                                         │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Optional note about how this workout felt...                            │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────────┤
│ Warmup                                                                       │
│ Exercise                         Type        Prescription       Actions      │
│ Bodyweight Squat                 STRENGTH    2 x 12             [Add Current]│
│                                                                              │
│ Main                                                                         │
│ Barbell Flat Bench Press          STRENGTH    3 x 10 @ 84 kg     [Add Current]│
│ One Arm Dumbbell Row              STRENGTH    3 x 10 @ 24 kg     [Add Current]│
│                                                                              │
│ Cooldown                                                                     │
│ Walking                           CARDIO      300 sec            [Add Current]│
└──────────────────────────────────────────────────────────────────────────────┘
```

Required behavior:

- Fetch by workout ID using the existing workout detail endpoint.
- Group sequences by `warmup`, `main`, and `cooldown`.
- Sort sequences and sets by `position`.
- Show exercise ID for dataset traceability.
- Prefer showing exercise name by joining against `/exercises`; if unavailable, show the ID.
- Include a top-level `Replay All` action that starts a new/current workout from the full workout.
- Include an `Add Current` action beside each exercise to add that movement to the current workout.
- Include a 1-5 analog enjoyment rating control from sad to happy.
- Include an optional free-text note for subjective workout feedback.
- Show not-found and error states.

## New Workout Page

```txt
┌──────────────────────────────────────────────────────────────────────────────┐
│ ← Workouts                                                                   │
│ New Workout                                                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────┐ ┌─────────────────────────┐ │
│ │ Workout Chat                                 │ │ Current Sequence        │ │
│ │                                              │ │ Warmup                  │ │
│ │ Assistant                                    │ │ • Bodyweight Squat      │ │
│ │ What are we training today?                  │ │                         │ │
│ │                                              │ │ Main                    │ │
│ │ You                                          │ │ • Bench Press           │ │
│ │ Upper body, 30 minutes, dumbbells            │ │ • One Arm Row           │ │
│ │                                              │ │                         │ │
│ │ Assistant                                    │ │ Cooldown                │ │
│ │ I added a warmup, main block, and cooldown.  │ │ • Walking               │ │
│ │                                              │ │                         │ │
│ │ ┌──────────────────────────────────────────┐ │ │ [Save Workout]          │ │
│ │ │ Tell the coach what to build or change...│ │ │                         │ │
│ │ └──────────────────────────────────────────┘ │ │                         │ │
│ │                                  [Send]      │ │                         │ │
│ └──────────────────────────────────────────────┘ └─────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

Required behavior:

- Replace the manual form as the primary experience with a chat-first workout builder.
- Keep the workout sequence visible beside the chat so the user can see what the agent is changing.
- The sequence panel should group the current workout by `warmup`, `main`, and `cooldown`.
- Agent replies should be able to add, modify, or remove current workout items as the backend supports it.
- Manual controls can remain as secondary/debug affordances if needed, but should not be the dominant UI.
- On success, redirect to the created workout details page if possible; otherwise redirect to `/workouts`.

## Exercises Page

```txt
┌──────────────────────────────────────────────────────────────────────────────┐
│ Exercises                                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ Name filter          Muscle filter              Equipment filter             │
│ ┌───────────────┐    ┌─────────────────────┐    ┌─────────────────────┐     │
│ │ bench         │    │ chest,triceps       │    │ barbell             │     │
│ └───────────────┘    └─────────────────────┘    └─────────────────────┘     │
├──────────────────────────────────────────────────────────────────────────────┤
│ Name                          Category       Muscle groups       Equipment   │
│ Barbell Flat Bench Press       strength       chest, triceps      [Add]       │
│ Dumbbell Bench Press           strength       chest, triceps      [Add]       │
└──────────────────────────────────────────────────────────────────────────────┘
```

Add exercise modal:

```txt
┌────────────────────────────────────────────┐
│ Add Barbell Flat Bench Press               │
│                                            │
│ Sets        [3]                            │
│ Reps        [10]                           │
│ Weight      [185] [lb v]                   │
│                                            │
│ Warnings                                   │
│ This exercise uses barbell equipment.      │
│                                            │
│ [Cancel]                         [Add]     │
└────────────────────────────────────────────┘
```

Required behavior:

- Keep this page as the dataset reference for grounding.
- Search/filter by name, muscle group, and equipment.
- Include an `Add` action next to each exercise to add it to the current workout.
- Pressing `Add` opens an agent-assisted modal that asks for required prescription details such as sets, reps, duration, and weight.
- The modal displays warnings when applicable, such as missing equipment fit, unsupported weight, uncertain constraints, or incomplete prescription details.
- Show empty, loading, and error states.
- Include exercise IDs in a compact secondary position if useful for assessor traceability.

## Mobile Layout Notes

```txt
┌──────────────────────────────┐
│ Workout Wiz             Menu │
├──────────────────────────────┤
│ Page title                   │
│ Primary action               │
│                              │
│ Stacked content blocks        │
│ Tables become card rows       │
│ Chat composer sticks bottom   │
└──────────────────────────────┘
```

Mobile requirements:

- The chat page remains the indexed/main page on mobile.
- On mobile chat, previous workout cards move from the right column to a horizontal row above the conversation.
- Chat composer remains reachable without covering the latest assistant response.
- Other pages can mostly follow the desktop information hierarchy with stacked sections where needed.
- Route/confidence badges wrap below sender labels instead of squeezing message text.

## Implementation Priority

1. Chat page.
2. Workout details page.
3. Workouts list row links.
4. Shared app shell/navigation.
5. Minor exercise page traceability polish.
6. Manual new workout redirect polish.
