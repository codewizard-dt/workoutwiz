/* ============================================================
   Workout details — grouped phases, enjoyment, note, replay.
   ============================================================ */
const FEEL_ICONS = ["frown", "annoyed", "meh", "smile", "laugh"];

function EnjoymentScale({ value, onChange }) {
  return (
    <div className="feel-row">
      <span className="feel-end">Sad</span>
      <div className="feel-scale">
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} className="feel-dot" data-on={value === n} aria-label={"Rate " + n}
            onClick={() => onChange(n)}>
            <Icon name={FEEL_ICONS[n - 1]} size={16} />
          </button>
        ))}
      </div>
      <span className="feel-end">Happy</span>
    </div>
  );
}

function PhaseTable({ seq, units, onAddCurrent }) {
  return (
    <div className="phase-block">
      <div className="phase-label">{PHASE_LABEL[seq.phase]}</div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead>
            <tr>
              <th style={{ width: "42%" }}>Exercise</th>
              <th>Type</th>
              <th>Prescription</th>
              <th style={{ textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {seq.sets.map((s) => {
              const ex = EX_BY_ID[s.exId] || { name: s.exId, id: s.exId };
              return (
                <tr key={s.id}>
                  <td data-label="Exercise">
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span className="ex-name">{ex.name}</span>
                      <span className="ex-id">{ex.id}</span>
                    </div>
                  </td>
                  <td data-label="Type"><Badge variant={s.type === "cardio" ? "amber" : s.type === "core" ? "secondary" : "soft"}>{s.type.toUpperCase()}</Badge></td>
                  <td data-label="Prescription" className="num">{fmtPrescription(s, units)}</td>
                  <td data-label="Actions" className="actions">
                    <Button variant="outline" size="sm" onClick={() => onAddCurrent(ex, s)}
                      iconStart={<Icon name="plus" size={14} />}>Add Current</Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function WorkoutDetails({ workout, navigate, units, onAddCurrent, onReplayAll }) {
  const [enjoyment, setEnjoyment] = React.useState(workout ? workout.enjoyment : 3);
  const [note, setNote] = React.useState(workout ? workout.note : "");

  React.useEffect(() => {
    if (workout) { setEnjoyment(workout.enjoyment); setNote(workout.note || ""); }
  }, [workout && workout.id]);

  if (!workout) {
    return (
      <div className="page page--narrow">
        <button className="backlink" onClick={() => navigate("workouts")}><Icon name="arrow-left" size={15} /> Workouts</button>
        <div className="empty-state">
          <img src="assets/logo-mascot.png" alt="" />
          <h3>Workout not found</h3>
          <p>We couldn't find that session — it may have been deleted.</p>
          <div className="empty-actions">
            <Button variant="gradient" onClick={() => navigate("workouts")} iconStart={<Icon name="arrow-left" size={15} color="#fff" />}>Back to workouts</Button>
          </div>
        </div>
      </div>
    );
  }

  const ordered = PHASES.map((p) => workout.sequences.find((s) => s.phase === p)).filter(Boolean);

  return (
    <div className="page">
      <button className="backlink" onClick={() => navigate("workouts")}><Icon name="arrow-left" size={15} /> Workouts</button>

      <div className="detail-head">
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-0.025em", margin: 0 }}>{workout.title}</h1>
          <div className="detail-times">
            <div><div className="k">Started</div><div className="v">{fmtDateTime(workout.startedAt)}</div></div>
            <div><div className="k">Ended</div><div className="v">{fmtDateTime(workout.endedAt)}</div></div>
            <div><div className="k">Workout ID</div><div className="v">{workout.id}</div></div>
          </div>
        </div>
        <Button variant="gradient" onClick={() => onReplayAll(workout)}
          iconStart={<Icon name="repeat" size={15} color="#fff" />}>Replay All</Button>
      </div>

      <Card style={{ margin: "20px 0 8px" }}>
        <CardContent style={{ display: "flex", flexDirection: "column", gap: 16, padding: 18 }}>
          <div>
            <div className="eyebrow" style={{ marginBottom: 8 }}>Enjoyment</div>
            <EnjoymentScale value={enjoyment} onChange={setEnjoyment} />
          </div>
          <Field label="Note" htmlFor="wknote">
            <Textarea id="wknote" rows={2} placeholder="Optional note about how this workout felt…"
              value={note} onChange={(e) => setNote(e.target.value)} />
          </Field>
        </CardContent>
      </Card>

      <div className="phase-table-wrap">
        {ordered.map((seq) => (
          <PhaseTable key={seq.phase} seq={seq} units={units} onAddCurrent={onAddCurrent} />
        ))}
      </div>
    </div>
  );
}

window.WorkoutDetails = WorkoutDetails;
