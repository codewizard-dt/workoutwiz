/* ============================================================
   Exercises — dataset reference library + agent-assisted Add.
   ============================================================ */
const ALL_MUSCLES = ["chest", "back", "shoulders", "quads", "glutes", "hamstrings", "biceps", "triceps", "core", "full body"];
const ALL_EQUIP = ["barbell", "dumbbell", "cable", "bodyweight", "band", "machine"];

function AddExerciseModal({ ex, units, onClose, onAdd }) {
  const isBodyweight = ex.equip.includes("bodyweight");
  const isCardio = ex.category === "cardio";
  const [sets, setSets] = React.useState(isCardio ? 1 : 3);
  const [reps, setReps] = React.useState(isCardio ? "" : 10);
  const [weight, setWeight] = React.useState(isBodyweight || isCardio ? "" : (units === "lb" ? 135 : 60));
  const [duration, setDuration] = React.useState(isCardio ? 300 : "");

  const warnings = [];
  if (!isBodyweight && !isCardio && (weight === "" || Number(weight) <= 0))
    warnings.push("No working weight set — the coach will log this as bodyweight.");
  if (ex.equip.includes("barbell"))
    warnings.push(`Uses ${ex.equip.join(", ")} equipment — make sure it's available where you train.`);
  if (!isCardio && (reps === "" || Number(reps) <= 0))
    warnings.push("Reps are required to complete the prescription.");

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__head">
          <CoachGlyph size={30} />
          <h3>Add {ex.name}</h3>
        </div>
        <p className="modal__sub">{ex.id} · I'll add this to your current workout — confirm the prescription.</p>

        <div className="modal__grid">
          <label>Sets</label>
          <Input type="number" value={sets} min={1} onChange={(e) => setSets(e.target.value)} style={{ maxWidth: 110 }} />
          {!isCardio && <React.Fragment>
            <label>Reps</label>
            <Input type="number" value={reps} placeholder="10" onChange={(e) => setReps(e.target.value)} style={{ maxWidth: 110 }} />
          </React.Fragment>}
          {isCardio ? <React.Fragment>
            <label>Duration</label>
            <div className="qty"><Input type="number" value={duration} onChange={(e) => setDuration(e.target.value)} style={{ maxWidth: 110 }} /><span className="muted" style={{ fontSize: 13 }}>sec</span></div>
          </React.Fragment> : !isBodyweight && <React.Fragment>
            <label>Weight</label>
            <div className="qty"><Input type="number" value={weight} onChange={(e) => setWeight(e.target.value)} style={{ maxWidth: 110 }} /><span className="muted" style={{ fontSize: 13 }}>{units}</span></div>
          </React.Fragment>}
        </div>

        {warnings.length > 0 && (
          <div className="modal__warn">
            <Icon name="triangle-alert" size={16} />
            <div>
              <div style={{ fontWeight: 600, marginBottom: 3 }}>Warnings</div>
              {warnings.map((w, i) => <div key={i} style={{ marginTop: i ? 4 : 0 }}>{w}</div>)}
            </div>
          </div>
        )}

        <div className="modal__actions">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button variant="gradient" onClick={() => onAdd({
            exId: ex.id, type: ex.category, sets: Number(sets) || 1,
            reps: isCardio ? null : (Number(reps) || null),
            weight: isCardio || isBodyweight ? null : (Number(weight) || null),
            duration: isCardio ? (Number(duration) || null) : null,
          })} iconStart={<Icon name="plus" size={15} color="#fff" />}>Add to workout</Button>
        </div>
      </div>
    </div>
  );
}

function Exercises({ navigate, units, onAddCurrent }) {
  const [loading, setLoading] = React.useState(true);
  const [q, setQ] = React.useState("");
  const [muscles, setMuscles] = React.useState([]);
  const [equip, setEquip] = React.useState([]);
  const [modalEx, setModalEx] = React.useState(null);

  React.useEffect(() => { const t = setTimeout(() => setLoading(false), 550); return () => clearTimeout(t); }, []);

  const toggle = (arr, set, v) => set(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

  const rows = EXERCISES.filter((e) => {
    const mq = !q || e.name.toLowerCase().includes(q.toLowerCase());
    const mm = muscles.length === 0 || e.muscles.some((m) => muscles.includes(m));
    const me = equip.length === 0 || e.equip.some((m) => equip.includes(m));
    return mq && mm && me;
  });

  return (
    <div className="page">
      <div className="page-head"><div><h1>Exercises</h1><p>The movement dataset used to ground every plan and log.</p></div></div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 16 }}>
        <div style={{ maxWidth: 320 }}>
          <Input placeholder="Search by name…" value={q} onChange={(e) => setQ(e.target.value)} icon={<Icon name="search" size={16} />} />
        </div>
        <div>
          <div className="eyebrow" style={{ marginBottom: 6 }}>Muscle group</div>
          <div className="chips-row" style={{ margin: 0 }}>
            {ALL_MUSCLES.map((m) => (
              <button key={m} className="chip" onClick={() => toggle(muscles, setMuscles, m)}
                style={muscles.includes(m) ? { background: "var(--acc-solid)", color: "#fff", borderColor: "var(--acc-solid)" } : {}}>{m}</button>
            ))}
          </div>
        </div>
        <div>
          <div className="eyebrow" style={{ marginBottom: 6 }}>Equipment</div>
          <div className="chips-row" style={{ margin: 0 }}>
            {ALL_EQUIP.map((m) => (
              <button key={m} className="chip" onClick={() => toggle(equip, setEquip, m)}
                style={equip.includes(m) ? { background: "var(--acc-solid)", color: "#fff", borderColor: "var(--acc-solid)" } : {}}>{m}</button>
            ))}
          </div>
        </div>
        {(muscles.length > 0 || equip.length > 0 || q) && (
          <button className="backlink" style={{ margin: 0, alignSelf: "flex-start" }}
            onClick={() => { setQ(""); setMuscles([]); setEquip([]); }}><Icon name="x" size={14} /> Clear filters</button>
        )}
      </div>

      {loading ? (
        <div className="tbl-wrap" style={{ padding: 16 }}>
          {[0, 1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 44, marginBottom: 10 }} />)}
        </div>
      ) : rows.length === 0 ? (
        <div className="empty-state">
          <img src="assets/logo-mascot.png" alt="" />
          <h3>No exercises match</h3>
          <p>Try a different name, muscle group, or equipment filter.</p>
          <div className="empty-actions"><Button variant="outline" onClick={() => { setQ(""); setMuscles([]); setEquip([]); }}>Clear filters</Button></div>
        </div>
      ) : (
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr><th style={{ width: "36%" }}>Name</th><th>Category</th><th>Muscle groups</th><th>Equipment</th><th style={{ textAlign: "right" }}>Actions</th></tr>
            </thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.id}>
                  <td data-label="Name">
                    <div style={{ display: "flex", alignItems: "center" }}>
                      <span className="tier-dot" style={{ background: TIER_COLOR[e.tier] }} />
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        <span className="ex-name">{e.name}</span>
                        <span className="ex-id">{e.id}</span>
                      </div>
                    </div>
                  </td>
                  <td data-label="Category"><Badge variant={e.category === "cardio" ? "amber" : e.category === "core" ? "secondary" : "soft"}>{e.category}</Badge></td>
                  <td data-label="Muscles" className="muted">{e.muscles.join(", ")}</td>
                  <td data-label="Equipment" className="muted">{e.equip.join(", ")}</td>
                  <td data-label="Actions" className="actions">
                    <Button variant="outline" size="sm" onClick={() => setModalEx(e)} iconStart={<Icon name="plus" size={14} />}>Add</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="muted" style={{ fontSize: 12, marginTop: 12, display: "flex", gap: 16, flexWrap: "wrap" }}>
        <span><span className="tier-dot" style={{ background: TIER_COLOR[1] }} />Tier 1 — compound</span>
        <span><span className="tier-dot" style={{ background: TIER_COLOR[2] }} />Tier 2 — accessory</span>
        <span><span className="tier-dot" style={{ background: TIER_COLOR[3] }} />Tier 3 — isolation</span>
      </p>

      {modalEx && (
        <AddExerciseModal ex={modalEx} units={units} onClose={() => setModalEx(null)}
          onAdd={(presc) => { onAddCurrent(EX_BY_ID[presc.exId], presc); setModalEx(null); }} />
      )}
    </div>
  );
}

window.Exercises = Exercises;
window.AddExerciseModal = AddExerciseModal;
