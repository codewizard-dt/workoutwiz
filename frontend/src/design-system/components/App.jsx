/* ============================================================
   App — router, store, and Tweaks.
   ============================================================ */
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "ember",
  "chatVariant": "split",
  "units": "kg"
}/*EDITMODE-END*/;

const VARIANT_LABEL = {
  split: "Split — chat + previous workouts (spec)",
  centered: "Centered — focused single column",
  trace: "Trace-forward — agent traces expanded",
};

function useHashRoute(authed) {
  const parse = () => (window.location.hash || "").replace(/^#\/?/, "") || (authed ? "chat" : "login");
  const [route, setRoute] = React.useState(parse);
  React.useEffect(() => {
    const on = () => setRoute(parse());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, [authed]);
  const navigate = (r) => {
    if (("#/" + r) === window.location.hash) setRoute(r);
    else window.location.hash = "/" + r;
  };
  return [route, navigate, setRoute];
}

function defaultPresc(ex) {
  const cardio = ex.category === "cardio";
  const bw = ex.equip.includes("bodyweight");
  return { exId: ex.id, type: ex.category, sets: cardio ? 1 : 3,
    reps: cardio ? null : 10, weight: cardio || bw ? null : 20, duration: cardio ? 300 : null };
}

let _wkSeq = 2042;

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [authed, setAuthed] = React.useState(false);
  const [route, navigate] = useHashRoute(authed);
  const [workouts, setWorkouts] = React.useState(WORKOUTS);
  const [draft, setDraft] = React.useState([]);
  const [toast, setToast] = React.useState(null);
  const sessionId = React.useMemo(() => {
    let s = localStorage.getItem("ww_session");
    if (!s) { s = "sess_" + Math.random().toString(36).slice(2, 8); localStorage.setItem("ww_session", s); }
    return s;
  }, []);

  const units = t.units;
  const setUnits = (u) => setTweak("units", u);

  function showToast(message, action) {
    setToast({ message, action });
    clearTimeout(window.__wwToast);
    window.__wwToast = setTimeout(() => setToast(null), 2800);
  }

  function addCurrent(ex, presc) {
    const p = presc || defaultPresc(ex);
    const phase = ex.category === "cardio" ? "cooldown" : "main";
    setDraft((d) => [...d, { key: "d" + Date.now() + Math.random(), phase, ...p }]);
    showToast(`Added ${ex.name} to current workout`, { label: "View", run: () => navigate("workouts/new") });
  }

  function replayAll(wk) {
    const items = [];
    wk.sequences.forEach((seq) => seq.sets.forEach((s) =>
      items.push({ key: "d" + Date.now() + Math.random() + s.id, phase: seq.phase, exId: s.exId,
        reps: s.reps, sets: s.sets, weight: s.weight, duration: s.duration, type: s.type })));
    setDraft(items);
    navigate("workouts/new");
    showToast("Loaded workout into the builder");
  }

  function saveWorkout(items) {
    if (!items.length) return;
    const id = "wk_" + (++_wkSeq);
    const sequences = PHASES.map((p) => ({ phase: p,
      sets: items.filter((i) => i.phase === p).map((i, idx) => ({ id: id + "_" + idx, exId: i.exId,
        type: i.type || "strength", reps: i.reps, sets: i.sets, weight: i.weight, duration: i.duration })) }))
      .filter((s) => s.sets.length);
    const now = new Date();
    const wk = { id, startedAt: now.toISOString(), endedAt: new Date(now.getTime() + 33 * 60000).toISOString(),
      title: "Logged workout", enjoyment: 4, note: "", sequences };
    setWorkouts((w) => [wk, ...w]);
    setDraft([]);
    navigate("workout/" + id);
    showToast("Workout saved");
  }

  function deleteWorkout(id) {
    setWorkouts((w) => w.filter((x) => x.id !== id));
    showToast("Workout deleted");
  }

  const panel = (
    <TweaksPanel>
      <TweakSection label="Brand" />
      <TweakColor label="Accent" value={t.accent === "amber" ? "#C77B1E" : "#D24317"}
        options={["#D24317", "#C77B1E"]}
        onChange={(v) => setTweak("accent", v === "#C77B1E" ? "amber" : "ember")} />
      <TweakSection label="Chat layout" />
      <TweakSelect label="Variant" value={t.chatVariant}
        options={Object.keys(VARIANT_LABEL).map((k) => ({ value: k, label: VARIANT_LABEL[k] }))}
        onChange={(v) => setTweak("chatVariant", v)} />
      <TweakSection label="Units" />
      <TweakRadio label="Weight" value={t.units} options={["kg", "lb"]} onChange={(v) => setTweak("units", v)} />
    </TweaksPanel>
  );

  // ---- unauthenticated ----
  if (!authed) {
    if (route === "register")
      return (<div data-accent={t.accent}>
        <RegisterScreen accent={t.accent} onRegister={() => { setAuthed(true); navigate("chat"); }} goLogin={() => navigate("login")} />
        {panel}
      </div>);
    return (<div data-accent={t.accent}>
      <LoginScreen accent={t.accent} onLogin={() => { setAuthed(true); navigate("chat"); }} goRegister={() => navigate("register")} />
      {panel}
    </div>);
  }

  // ---- authenticated routing ----
  let content;
  if (route === "workouts") content = <WorkoutsScreen workouts={workouts} navigate={navigate} onDelete={deleteWorkout} />;
  else if (route === "workouts/new") content = <NewWorkout draft={draft} setDraft={setDraft} navigate={navigate} units={units} onSave={saveWorkout} />;
  else if (route.startsWith("workout/")) {
    const id = route.split("/")[1];
    content = <WorkoutDetails workout={workouts.find((w) => w.id === id)} navigate={navigate} units={units} onAddCurrent={addCurrent} onReplayAll={replayAll} />;
  }
  else if (route === "exercises") content = <Exercises navigate={navigate} units={units} onAddCurrent={addCurrent} />;
  else content = <ChatScreen navigate={navigate} units={units} variant={t.chatVariant} sessionId={sessionId} />;

  return (
    <div data-accent={t.accent}>
      <Shell route={route} navigate={navigate} units={units} setUnits={setUnits}
        onLogout={() => { setAuthed(false); navigate("login"); }}>
        {content}
      </Shell>
      {toast && (
        <div className="toast">
          <Icon name="check-circle-2" size={16} /> {toast.message}
          {toast.action && <button onClick={() => { toast.action.run(); setToast(null); }}
            style={{ background: "none", border: "none", color: "var(--amber-400)", fontWeight: 600, cursor: "pointer", fontSize: 13.5 }}>{toast.action.label}</button>}
        </div>
      )}
      {panel}
    </div>
  );
}

window.App = App;
