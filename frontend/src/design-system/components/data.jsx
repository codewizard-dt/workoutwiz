/* ============================================================
   Workout Wiz — shared data, helpers, and app store.
   ============================================================ */

/* ---- Lucide icon → React element ---- */
function Icon({ name, size = 18, color, style, strokeWidth = 1.75 }) {
  const node = lucide[name] ? lucide.createElement(lucide[name]) : null;
  if (!node) return null;
  node.setAttribute("width", size);
  node.setAttribute("height", size);
  node.setAttribute("stroke-width", strokeWidth);
  return (
    <span style={{ display: "inline-flex", color, ...style }}
      dangerouslySetInnerHTML={{ __html: node.outerHTML }} />
  );
}

function CoachGlyph({ size = 36 }) {
  return (
    <span className="ww-coach-avatar" style={{ width: size, height: size }}>
      <img src="assets/logo-mascot.png" alt="Wiz" style={{ width: size * 0.66, height: size * 0.66 }} />
    </span>
  );
}

/* ---- Exercise library (dataset reference) ---- */
const EXERCISES = [
  { id: "ex_001", name: "Barbell Flat Bench Press", category: "strength", muscles: ["chest", "triceps"], equip: ["barbell"], tier: 1 },
  { id: "ex_002", name: "Dumbbell Bench Press", category: "strength", muscles: ["chest", "triceps"], equip: ["dumbbell"], tier: 1 },
  { id: "ex_003", name: "Back Squat", category: "strength", muscles: ["quads", "glutes"], equip: ["barbell"], tier: 1 },
  { id: "ex_004", name: "Conventional Deadlift", category: "strength", muscles: ["back", "hamstrings", "glutes"], equip: ["barbell"], tier: 1 },
  { id: "ex_005", name: "One Arm Dumbbell Row", category: "strength", muscles: ["back", "biceps"], equip: ["dumbbell"], tier: 2 },
  { id: "ex_006", name: "Overhead Press", category: "strength", muscles: ["shoulders", "triceps"], equip: ["barbell"], tier: 2 },
  { id: "ex_007", name: "Pull-up", category: "strength", muscles: ["back", "biceps"], equip: ["bodyweight"], tier: 1 },
  { id: "ex_008", name: "Dumbbell Bicep Curl", category: "strength", muscles: ["biceps"], equip: ["dumbbell"], tier: 3 },
  { id: "ex_009", name: "Romanian Deadlift", category: "strength", muscles: ["hamstrings", "glutes"], equip: ["barbell"], tier: 2 },
  { id: "ex_010", name: "Incline Dumbbell Press", category: "strength", muscles: ["chest", "shoulders"], equip: ["dumbbell"], tier: 2 },
  { id: "ex_011", name: "Lat Pulldown", category: "strength", muscles: ["back"], equip: ["cable"], tier: 3 },
  { id: "ex_012", name: "Triceps Pushdown", category: "strength", muscles: ["triceps"], equip: ["cable"], tier: 3 },
  { id: "ex_013", name: "Bodyweight Squat", category: "strength", muscles: ["quads", "glutes"], equip: ["bodyweight"], tier: 2 },
  { id: "ex_014", name: "Band Pull-apart", category: "strength", muscles: ["shoulders", "back"], equip: ["band"], tier: 3 },
  { id: "ex_015", name: "Walking", category: "cardio", muscles: ["full body"], equip: ["bodyweight"], tier: 2 },
  { id: "ex_016", name: "Treadmill Run", category: "cardio", muscles: ["full body"], equip: ["machine"], tier: 2 },
  { id: "ex_017", name: "Plank", category: "core", muscles: ["core"], equip: ["bodyweight"], tier: 3 },
  { id: "ex_018", name: "Arm Circles", category: "mobility", muscles: ["shoulders"], equip: ["bodyweight"], tier: 3 },
];
const EX_BY_ID = Object.fromEntries(EXERCISES.map((e) => [e.id, e]));
const TIER_COLOR = { 1: "var(--ember-500)", 2: "var(--amber-500)", 3: "var(--stone-400)" };

/* ---- Saved workouts (each → sequences[phase] → sets[position]) ---- */
const WORKOUTS = [
  {
    id: "wk_2041", startedAt: "2026-06-06T08:30:00", endedAt: "2026-06-06T09:04:00",
    title: "Upper Body · Push", enjoyment: 4, note: "Bench felt strong — moved up 2.5 kg on top set.",
    sequences: [
      { phase: "warmup", sets: [
        { id: "s1", exId: "ex_018", type: "strength", reps: 12, sets: 2, weight: null, duration: null },
        { id: "s2", exId: "ex_014", type: "strength", reps: 15, sets: 2, weight: null, duration: null },
      ]},
      { phase: "main", sets: [
        { id: "s3", exId: "ex_001", type: "strength", reps: 10, sets: 3, weight: 84, duration: null },
        { id: "s4", exId: "ex_006", type: "strength", reps: 8, sets: 3, weight: 40, duration: null },
        { id: "s5", exId: "ex_010", type: "strength", reps: 12, sets: 3, weight: 22, duration: null },
        { id: "s6", exId: "ex_012", type: "strength", reps: 15, sets: 3, weight: 30, duration: null },
      ]},
      { phase: "cooldown", sets: [
        { id: "s7", exId: "ex_015", type: "cardio", reps: null, sets: 1, weight: null, duration: 300 },
      ]},
    ],
  },
  {
    id: "wk_2038", startedAt: "2026-06-05T18:15:00", endedAt: "2026-06-05T18:46:00",
    title: "Quick Log · Cardio", enjoyment: 3, note: "",
    sequences: [
      { phase: "main", sets: [
        { id: "s1", exId: "ex_016", type: "cardio", reps: null, sets: 1, weight: null, duration: 1200 },
        { id: "s2", exId: "ex_017", type: "core", reps: null, sets: 3, weight: null, duration: 45 },
      ]},
    ],
  },
  {
    id: "wk_2031", startedAt: "2026-06-03T07:05:00", endedAt: "2026-06-03T07:58:00",
    title: "Lower Body · Strength", enjoyment: 5, note: "PR on squat. Legs cooked.",
    sequences: [
      { phase: "warmup", sets: [
        { id: "s1", exId: "ex_013", type: "strength", reps: 15, sets: 2, weight: null, duration: null },
      ]},
      { phase: "main", sets: [
        { id: "s2", exId: "ex_003", type: "strength", reps: 5, sets: 5, weight: 100, duration: null },
        { id: "s3", exId: "ex_009", type: "strength", reps: 8, sets: 3, weight: 70, duration: null },
      ]},
      { phase: "cooldown", sets: [
        { id: "s4", exId: "ex_015", type: "cardio", reps: null, sets: 1, weight: null, duration: 420 },
      ]},
    ],
  },
];

const PHASES = ["warmup", "main", "cooldown"];
const PHASE_LABEL = { warmup: "Warmup", main: "Main", cooldown: "Cooldown" };

/* ---- Multi-agent routing metadata ---- */
const ROUTE_META = {
  COACH:            { label: "COACH",            icon: "message-circle-question", tone: "info" },
  KNOWLEDGE_GRAPH: { label: "KNOWLEDGE_GRAPH", icon: "sparkles",                tone: "ember" },
  WORKOUT_LOG:      { label: "WORKOUT_LOG",       icon: "clipboard-check",         tone: "amber" },
  FALLBACK:         { label: "FALLBACK",          icon: "help-circle",             tone: "stone" },
};

function classifyIntent(t) {
  const s = (t || "").toLowerCase();
  if (/(did|logged|completed|i just|finished|i ran|\bran\b|@|\bx\s?\d|\d+\s*reps|\d+\s*sets)/.test(s)) return { route: "WORKOUT_LOG", conf: 0.92 };
  if (/(build|generate|plan|design|program|give me|make me|create|workout for|session|routine|\d+\s*min|dumbbell|barbell|kettlebell|upper body|lower body|full body|push day|pull day|leg day)/.test(s)) return { route: "KNOWLEDGE_GRAPH", conf: 0.95 };
  if (/(how|why|what|should|which|many|rest|muscle|work|target|good for)/.test(s)) return { route: "COACH", conf: 0.94 };
  return { route: "FALLBACK", conf: 0.61 };
}

/* Build the expandable agent-trace timeline for a routed turn. */
function buildTrace(route, conf) {
  const router = { agent: "Router", route, detail: `Classified intent → ${route}`, conf, ms: 78, status: "ok" };
  if (route === "KNOWLEDGE_GRAPH") {
    return [
      router,
      { agent: "Exercise DB", detail: "Queried library · matched equipment {dumbbell, barbell}", ms: 142, status: "ok", meta: "18 candidates → 6 selected" },
      { agent: "Planner agent", detail: "Assembled warmup · main · cooldown", ms: 410, status: "ok" },
      { agent: "Volume check", detail: "Projected session volume", ms: 36, status: "ok", meta: "≈ 1,840 kg" },
    ];
  }
  if (route === "WORKOUT_LOG") {
    return [
      router,
      { agent: "Parser agent", detail: "Extracted sets from natural language", ms: 196, status: "ok", meta: "bench 3×10 @ 60 kg · run 20 min" },
      { agent: "Exercise DB", detail: "Resolved exercise IDs", ms: 88, status: "ok", meta: "ex_001, ex_016" },
      { agent: "DB write", detail: "Created workout record", ms: 124, status: "ok", meta: "wk_2042" },
    ];
  }
  if (route === "COACH") {
    return [
      router,
      { agent: "Knowledge agent", detail: "Composed answer from training KB", ms: 322, status: "ok" },
      { agent: "Guardrail", detail: "Scope + safety check passed", ms: 41, status: "ok" },
    ];
  }
  return [
    { agent: "Router", route, detail: "No confident intent match", conf, ms: 80, status: "warn" },
    { agent: "Guardrail", detail: "Redirected to in-scope capabilities", ms: 38, status: "ok" },
  ];
}

/* ---- Canned coach replies ---- */
const GEN_SESSION = {
  title: "Upper Body · Push",
  meta: "~45 min · 6 movements · dumbbell & barbell",
  sequences: [
    { phase: "warmup", sets: [
      { exId: "ex_018", reps: 12, sets: 2, weight: null, duration: null },
      { exId: "ex_014", reps: 15, sets: 2, weight: null, duration: null },
    ]},
    { phase: "main", sets: [
      { exId: "ex_001", reps: 10, sets: 3, weight: 60, duration: null },
      { exId: "ex_006", reps: 8, sets: 3, weight: 40, duration: null },
      { exId: "ex_010", reps: 12, sets: 3, weight: 22, duration: null },
      { exId: "ex_012", reps: 15, sets: 3, weight: 30, duration: null },
    ]},
    { phase: "cooldown", sets: [
      { exId: "ex_015", reps: null, sets: 1, weight: null, duration: 300 },
    ]},
  ],
};

function coachReply(route, conf) {
  const trace = buildTrace(route, conf);
  if (route === "KNOWLEDGE_GRAPH")
    return { from: "coach", route, conf, latency: 1.62, trace,
      text: "Here's a session tuned to your push day and the equipment in your profile. Want me to drop it into a new workout?",
      workout: GEN_SESSION };
  if (route === "WORKOUT_LOG")
    return { from: "coach", route, conf, latency: 2.08, trace,
      text: "Logged — bench press 3×10 @ 60 kg plus a 20-min run. Nice work; that's 1,800 kg of volume on chest today." };
  if (route === "COACH")
    return { from: "coach", route, conf, latency: 0.41, trace,
      text: "For hypertrophy most lifters do well with 1–2 rest days a week, training each muscle group about twice with ~48h between sessions. Recovery is where the growth happens." };
  return { from: "coach", route: "FALLBACK", conf, latency: 0.38, trace,
    text: "I'm your fitness coach — I can plan workouts, answer training questions, and log your sessions. Ask me anything in that lane." };
}

/* ---- Formatting helpers ---- */
const KG_PER_LB = 0.45359237;
function fmtWeight(kg, units) {
  if (kg == null) return null;
  if (units === "lb") return { value: Math.round(kg / KG_PER_LB), unit: "lb" };
  return { value: kg, unit: "kg" };
}
function fmtDuration(sec) {
  if (sec == null) return null;
  if (sec >= 60) {
    const m = Math.floor(sec / 60), s = sec % 60;
    return s ? `${m}:${String(s).padStart(2, "0")}` : `${m} min`;
  }
  return `${sec} sec`;
}
function fmtPrescription(set, units) {
  if (set.duration != null && set.reps == null) return fmtDuration(set.duration);
  const reps = set.reps != null ? `${set.sets || 1} × ${set.reps}` : `${set.sets || 1} sets`;
  if (set.weight != null) { const w = fmtWeight(set.weight, units); return `${reps} @ ${w.value} ${w.unit}`; }
  return reps;
}
function workoutStats(wk) {
  let sets = 0;
  wk.sequences.forEach((seq) => seq.sets.forEach((s) => { sets += (s.sets || 1); }));
  return { phases: wk.sequences.length, sets };
}
function fmtDateTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" });
}
function fmtDateShort(iso) {
  const d = new Date(iso);
  return d.toLocaleString("en-US", { month: "short", day: "numeric" });
}

Object.assign(window, {
  Icon, CoachGlyph, EXERCISES, EX_BY_ID, TIER_COLOR, WORKOUTS, PHASES, PHASE_LABEL,
  ROUTE_META, classifyIntent, buildTrace, coachReply, GEN_SESSION,
  fmtWeight, fmtDuration, fmtPrescription, workoutStats, fmtDateTime, fmtDateShort,
});
