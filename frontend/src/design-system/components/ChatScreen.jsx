/* ============================================================
   Chat — signature multi-agent coach surface.
   Shared pieces (RouteBadge, AgentTrace, AgentReply) are reused
   by the New Workout builder chat too.
   ============================================================ */

function RouteBadge({ route }) {
  const m = ROUTE_META[route] || ROUTE_META.FALLBACK;
  return (
    <span className="route-badge" data-tone={m.tone}>
      <Icon name={m.icon} size={12} /> {m.label}
    </span>
  );
}

function AgentTrace({ steps, defaultOpen }) {
  const [open, setOpen] = React.useState(!!defaultOpen);
  return (
    <div>
      <button className="trace-toggle" data-open={open} onClick={() => setOpen((v) => !v)}>
        <span className="chev"><Icon name="chevron-right" size={13} strokeWidth={2} /></span>
        <Icon name="route" size={13} />
        {open ? "Hide agent trace" : "Show agent trace"}
        <span className="ww-num" style={{ opacity: 0.6 }}>· {steps.length} steps</span>
      </button>
      {open && (
        <div className="trace">
          <div className="trace__title">Agent routing trace</div>
          {steps.map((s, i) => (
            <div key={i} className="trace__step" data-status={s.status}>
              <span className="trace__dot" />
              <div>
                <div className="trace__agent">
                  {s.agent}
                  {s.route && <RouteBadge route={s.route} />}
                  {s.conf != null && <span className="conf">conf {s.conf.toFixed(2)}</span>}
                </div>
                <div className="trace__detail">{s.detail}</div>
                {s.meta && <div className="trace__meta">{s.meta}</div>}
              </div>
              <span className="trace__ms">{s.ms} ms</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function setMetrics(set, units) {
  const m = [];
  if (set.reps != null) m.push({ value: `${set.sets || 1}×${set.reps}`, unit: "reps" });
  if (set.weight != null) { const w = fmtWeight(set.weight, units); m.push({ value: w.value, unit: w.unit }); }
  if (set.duration != null) m.push({ value: fmtDuration(set.duration), unit: "" });
  return m;
}

function GeneratedWorkoutCard({ session, units, onUse, used }) {
  return (
    <Card className="gen-card">
      <CardHeader>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Icon name="dumbbell" size={18} color="var(--acc-solid)" />
          <CardTitle>{session.title}</CardTitle>
        </div>
        <CardDescription>{session.meta}</CardDescription>
      </CardHeader>
      <CardContent>
        {session.sequences.map((seq) => (
          <div key={seq.phase}>
            <div className="phase-label">{PHASE_LABEL[seq.phase]}</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {seq.sets.map((s, i) => {
                const ex = EX_BY_ID[s.exId];
                return <SetRow key={i} name={ex.name} sub={ex.muscles.slice(0, 2).join(" · ")}
                  metrics={setMetrics(s, units)} />;
              })}
            </div>
          </div>
        ))}
      </CardContent>
      <CardFooter>
        <Button variant={used ? "secondary" : "primary"} size="sm" onClick={onUse}
          iconStart={<Icon name={used ? "check" : "plus"} size={15} />}>
          {used ? "Opened in builder" : "Start workout from this"}
        </Button>
        <Button variant="ghost" size="sm" iconStart={<Icon name="refresh-cw" size={15} />}>Regenerate</Button>
      </CardFooter>
    </Card>
  );
}

function AgentReply({ msg, units, traceDefaultOpen, onUseWorkout, usedWorkout }) {
  return (
    <ChatBubble from="coach" avatar={<CoachGlyph />}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 7 }}>
        <RouteBadge route={msg.route} />
        <span className="conf">confidence {msg.conf.toFixed(2)}</span>
        <span className="conf" style={{ opacity: 0.6 }}>· {msg.latency.toFixed(2)}s</span>
      </div>
      <div style={{ lineHeight: 1.55 }}>{msg.text}</div>
      {msg.workout && <GeneratedWorkoutCard session={msg.workout} units={units} onUse={onUseWorkout} used={usedWorkout} />}
      <AgentTrace steps={msg.trace} defaultOpen={traceDefaultOpen} />
    </ChatBubble>
  );
}

function PreviousWorkouts({ navigate }) {
  return (
    <div className="chat__panel">
      <div className="panel-title"><span>Previous workouts</span><a onClick={() => navigate("workouts")}>All workouts</a></div>
      <div className="panel-stack" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {WORKOUTS.slice(0, 3).map((wk) => {
          const st = workoutStats(wk);
          return (
            <Card key={wk.id} className="mini-wk" interactive onClick={() => navigate("workout/" + wk.id)}>
              <CardContent style={{ padding: 14 }}>
                <div className="mini-wk__date"><Icon name="calendar-check" size={13} /> {fmtDateShort(wk.startedAt)}</div>
                <div className="mini-wk__title">{wk.title}</div>
                <div className="mini-wk__stats">{st.phases} phases · {st.sets} sets</div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

const CHAT_PROMPTS = [
  { icon: "activity", text: "What muscles does a deadlift work?", route: "COACH" },
  { icon: "sparkles", text: "Build me a 30-min upper-body dumbbell session", route: "KNOWLEDGE_GRAPH" },
  { icon: "clipboard-check", text: "I did 3×10 bench at 60 kg and a 20-min run", route: "WORKOUT_LOG" },
  { icon: "dumbbell", text: "Is bench press enough for chest?", route: "COACH" },
];

function ChatScreen({ navigate, units, variant, sessionId }) {
  const [messages, setMessages] = React.useState([]);
  const [draft, setDraft] = React.useState("");
  const [thinking, setThinking] = React.useState(false);
  const [usedWorkout, setUsedWorkout] = React.useState(false);
  const streamRef = React.useRef(null);

  React.useEffect(() => {
    if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight;
  }, [messages, thinking]);

  function send(text, forcedRoute) {
    const t = (text || "").trim();
    if (!t) return;
    const { route, conf } = forcedRoute ? { route: forcedRoute, conf: classifyIntent(t).conf } : classifyIntent(t);
    setMessages((m) => [...m, { from: "user", text: t }]);
    setDraft("");
    setThinking(true);
    setTimeout(() => {
      setThinking(false);
      setMessages((m) => [...m, coachReply(route, conf)]);
    }, 620);
  }

  const traceOpen = variant === "trace";
  const showPanel = variant !== "centered";

  const stream = (
    <div className="chat__main">
      <div className="stream" ref={streamRef}>
        {messages.length === 0 && (
          <div className="chat-hero">
            <img src="assets/logo-mascot.png" alt="" />
            <h2>What are we training today?</h2>
            <p>Ask for a workout, log what you did, or get coaching — your AI strength coach routes each message to the right agent.</p>
          </div>
        )}
        {messages.map((m, i) =>
          m.from === "user"
            ? <ChatBubble key={i} from="user" avatar={<Avatar name="Morgan Vale" size="sm" />}>{m.text}</ChatBubble>
            : <AgentReply key={i} msg={m} units={units} traceDefaultOpen={traceOpen}
                onUseWorkout={() => { setUsedWorkout(true); navigate("workouts/new"); }} usedWorkout={usedWorkout} />
        )}
        {thinking && (
          <ChatBubble from="coach" avatar={<CoachGlyph />}>
            <span className="muted" style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 13 }}>
              <Icon name="loader-circle" size={14} style={{ animation: "spin 0.8s linear infinite" }} /> Routing…
            </span>
          </ChatBubble>
        )}
      </div>

      <div className="composer">
        {messages.length === 0 && (
          <div className="chips-row">
            {CHAT_PROMPTS.map((p, i) => (
              <button key={i} className="chip" onClick={() => send(p.text, p.route)}>
                <Icon name={p.icon} size={13} /> {p.text}
              </button>
            ))}
          </div>
        )}
        <div className="composer-box">
          <textarea rows={1} placeholder="Ask a question, request a workout, or log a session…"
            value={draft} onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(draft); } }} />
          <div className="composer-actions">
            {messages.length > 0 && (
              <IconButton aria-label="Clear conversation" variant="ghost" size="md" onClick={() => setMessages([])}>
                <Icon name="eraser" size={16} />
              </IconButton>
            )}
            <Button variant="gradient" size="md" onClick={() => send(draft)} disabled={!draft.trim()}
              iconStart={<Icon name="arrow-up" size={16} color="#fff" />} />
          </div>
        </div>
        <p className="composer-hint">
          Session <span className="ww-num">{sessionId}</span> · preserved across messages · routes to COACH / KNOWLEDGE_GRAPH / WORKOUT_LOG
        </p>
      </div>
    </div>
  );

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Chat</h1>
          <p>Ask questions, generate workouts, or log completed activity.</p>
        </div>
      </div>
      <div className={"chat" + (variant === "centered" ? " chat--centered" : "")}>
        {stream}
        {showPanel && <PreviousWorkouts navigate={navigate} />}
      </div>
    </div>
  );
}

window.RouteBadge = RouteBadge;
window.AgentTrace = AgentTrace;
window.AgentReply = AgentReply;
window.setMetrics = setMetrics;
window.ChatScreen = ChatScreen;
