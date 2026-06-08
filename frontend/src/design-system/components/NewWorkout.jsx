/* ============================================================
   New workout — chat-first builder with live sequence panel.
   The coach chat mutates the current workout (draft); the panel
   beside it shows what the agent is changing in real time.
   ============================================================ */
let _k = 0;
const nextKey = () => "d" + (++_k);

function genItems() {
  const out = [];
  GEN_SESSION.sequences.forEach((seq) =>
    seq.sets.forEach((s) => out.push({ key: nextKey(), phase: seq.phase, exId: s.exId,
      reps: s.reps, sets: s.sets, weight: s.weight, duration: s.duration,
      type: (EX_BY_ID[s.exId] || {}).category || "strength" })));
  return out;
}

function findExercise(text) {
  const s = text.toLowerCase();
  return EXERCISES.find((e) => s.includes(e.name.toLowerCase())) ||
    EXERCISES.find((e) => e.name.toLowerCase().split(" ").some((w) => w.length > 3 && s.includes(w)));
}

function NewWorkout({ draft, setDraft, navigate, units, onSave }) {
  const [messages, setMessages] = React.useState([
    { from: "coach", route: "COACH", conf: 0.99, latency: 0.2,
      text: "What are we training today? Tell me your goal, time, and equipment — or replay a past workout and I'll load it here.",
      trace: buildTrace("COACH", 0.99) },
  ]);
  const [input, setInput] = React.useState("");
  const [thinking, setThinking] = React.useState(false);
  const streamRef = React.useRef(null);

  React.useEffect(() => {
    if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight;
  }, [messages, thinking]);

  function coachTurn(text, forcedRoute) {
    const s = text.toLowerCase();
    const cls = classifyIntent(text);
    const route = forcedRoute || cls.route;
    const conf = cls.conf;

    if (route === "KNOWLEDGE_GRAPH" && !/(remove|drop|delete|take out|add|include|throw in)/.test(s)) {
      const items = genItems();
      setDraft(items);
      return { from: "coach", route, conf, latency: 1.5, trace: buildTrace("KNOWLEDGE_GRAPH", conf),
        text: "Done — I added a warmup, a main block of 4 lifts, and a cooldown. Adjust anything, or save when it looks right." };
    }
    if (/(remove|drop|delete|take out)/.test(s)) {
      let removed = null;
      setDraft((d) => { const copy = [...d]; removed = copy.pop(); return copy; });
      return { from: "coach", route: "KNOWLEDGE_GRAPH", conf: 0.88, latency: 0.7, trace: buildTrace("KNOWLEDGE_GRAPH", 0.88),
        text: removed ? "Removed the last movement from your sequence." : "Your sequence is already empty." };
    }
    if (/(add|include|throw in|put)/.test(s)) {
      const ex = findExercise(text) || EX_BY_ID["ex_005"];
      const phase = /(warm)/.test(s) ? "warmup" : /(cool|stretch|walk)/.test(s) ? "cooldown" : "main";
      const isCardio = ex.category === "cardio";
      setDraft((d) => [...d, { key: nextKey(), phase, exId: ex.id,
        reps: isCardio ? null : 10, sets: isCardio ? 1 : 3, weight: isCardio ? null : (ex.equip.includes("bodyweight") ? null : 20),
        duration: isCardio ? 300 : null, type: ex.category }]);
      return { from: "coach", route: "KNOWLEDGE_GRAPH", conf: 0.9, latency: 0.8, trace: buildTrace("KNOWLEDGE_GRAPH", 0.9),
        text: `Added ${ex.name} to your ${PHASE_LABEL[phase].toLowerCase()}.` };
    }
    // generic coaching
    return coachReply("COACH", conf);
  }

  function send(text, forcedRoute) {
    const t = (text || "").trim();
    if (!t) return;
    setMessages((m) => [...m, { from: "user", text: t }]);
    setInput("");
    setThinking(true);
    setTimeout(() => { setThinking(false); setMessages((m) => [...m, coachTurn(t, forcedRoute)]); }, 600);
  }

  const removeItem = (key) => setDraft((d) => d.filter((i) => i.key !== key));
  const grouped = PHASES.map((p) => ({ phase: p, items: draft.filter((i) => i.phase === p) })).filter((g) => g.items.length);
  const total = draft.length;

  const suggestions = [
    { text: "Upper body, 30 minutes, dumbbells", route: "KNOWLEDGE_GRAPH" },
    { text: "Add a cooldown walk", route: null },
    { text: "Remove the last movement", route: null },
  ];

  return (
    <div className="page">
      <button className="backlink" onClick={() => navigate("workouts")}><Icon name="arrow-left" size={15} /> Workouts</button>
      <div className="page-head"><div><h1>New Workout</h1><p>Tell the coach what to build — your sequence updates live on the right.</p></div></div>

      <div className="builder">
        <div className="builder__chat">
          <Card>
            <CardContent style={{ padding: 16 }}>
              <div className="stream" ref={streamRef} style={{ maxHeight: 420, overflowY: "auto", padding: "2px 2px 8px" }}>
                {messages.map((m, i) =>
                  m.from === "user"
                    ? <ChatBubble key={i} from="user" avatar={<Avatar name="Morgan Vale" size="sm" />}>{m.text}</ChatBubble>
                    : <AgentReply key={i} msg={m} units={units} />
                )}
                {thinking && (
                  <ChatBubble from="coach" avatar={<CoachGlyph />}>
                    <span className="muted" style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 13 }}>
                      <Icon name="loader-circle" size={14} style={{ animation: "spin 0.8s linear infinite" }} /> Working…
                    </span>
                  </ChatBubble>
                )}
              </div>
              <div className="chips-row" style={{ margin: "12px 0 0" }}>
                {suggestions.map((s, i) => <button key={i} className="chip" onClick={() => send(s.text, s.route)}>{s.text}</button>)}
              </div>
              <div className="composer-box" style={{ marginTop: 10 }}>
                <textarea rows={1} placeholder="Tell the coach what to build or change…"
                  value={input} onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }} />
                <Button variant="gradient" size="md" onClick={() => send(input)} disabled={!input.trim()}
                  iconStart={<Icon name="arrow-up" size={16} color="#fff" />} />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="builder__panel">
          <Card>
            <CardHeader>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <CardTitle>Current sequence</CardTitle>
                <span className="conf">{total} {total === 1 ? "item" : "items"}</span>
              </div>
            </CardHeader>
            <CardContent>
              {total === 0 ? (
                <div className="seq-empty">Nothing yet — ask the coach to build a session, or replay a past one.</div>
              ) : (
                grouped.map((g) => (
                  <div key={g.phase} className="seq-group">
                    <div className="seq-group__label">{PHASE_LABEL[g.phase]}</div>
                    {g.items.map((it) => {
                      const ex = EX_BY_ID[it.exId] || { name: it.exId };
                      return (
                        <div key={it.key} className="seq-item">
                          <Icon name="grip-vertical" size={14} color="var(--stone-400)" />
                          <span className="seq-item__name">{ex.name}</span>
                          <span className="seq-item__rx">{fmtPrescription(it, units)}</span>
                          <IconButton aria-label="Remove" variant="ghost" size="sm" onClick={() => removeItem(it.key)}>
                            <Icon name="x" size={14} />
                          </IconButton>
                        </div>
                      );
                    })}
                  </div>
                ))
              )}
            </CardContent>
            <CardFooter style={{ flexDirection: "column", alignItems: "stretch", gap: 8 }}>
              <Button variant="gradient" block disabled={total === 0} onClick={() => onSave(draft)}
                iconStart={<Icon name="save" size={16} color="#fff" />}>Save workout</Button>
              {total > 0 && <Button variant="ghost" size="sm" onClick={() => setDraft([])}>Clear all</Button>}
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
}

window.NewWorkout = NewWorkout;
