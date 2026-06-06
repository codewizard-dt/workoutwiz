/* ============================================================
   Workouts — list of saved workouts (rows link to details).
   ============================================================ */
function WorkoutsScreen({ workouts, navigate, onDelete }) {
  const [loading, setLoading] = React.useState(true);
  const [confirmId, setConfirmId] = React.useState(null);

  React.useEffect(() => {
    const t = setTimeout(() => setLoading(false), 650);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Workouts</h1>
          <p>Every session you've planned or logged. Tap a row to inspect it.</p>
        </div>
        <Button variant="gradient" onClick={() => navigate("workouts/new")}
          iconStart={<Icon name="plus" size={15} color="#fff" />}>New Workout</Button>
      </div>

      {loading ? (
        <div className="tbl-wrap" style={{ padding: 16 }}>
          {[0, 1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 46, marginBottom: 10 }} />)}
        </div>
      ) : workouts.length === 0 ? (
        <div className="empty-state">
          <img src="assets/logo-mascot.png" alt="" />
          <h3>No workouts yet</h3>
          <p>Ask the coach to build you a session, or start one from scratch.</p>
          <div className="empty-actions">
            <Button variant="gradient" onClick={() => navigate("chat")} iconStart={<Icon name="sparkles" size={15} color="#fff" />}>Ask the coach</Button>
            <Button variant="outline" onClick={() => navigate("workouts/new")} iconStart={<Icon name="plus" size={15} />}>New workout</Button>
          </div>
        </div>
      ) : (
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: "44%" }}>Date</th>
                <th>Phases</th>
                <th>Sets</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {workouts.map((wk) => {
                const st = workoutStats(wk);
                return (
                  <tr key={wk.id} className="clickable" onClick={() => navigate("workout/" + wk.id)}>
                    <td data-label="Date">
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        <span style={{ fontWeight: 600 }}>{fmtDateTime(wk.startedAt)}</span>
                        <span className="muted" style={{ fontSize: 12.5 }}>{wk.title}</span>
                      </div>
                    </td>
                    <td data-label="Phases" className="num">{st.phases}</td>
                    <td data-label="Sets" className="num">{st.sets}</td>
                    <td data-label="Actions" className="actions" onClick={(e) => e.stopPropagation()}>
                      <Button variant="outline" size="sm" onClick={() => navigate("workout/" + wk.id)}
                        iconStart={<Icon name="eye" size={14} />}>View</Button>
                      <IconButton aria-label="Delete workout" variant="ghost" size="sm" onClick={() => setConfirmId(wk.id)}>
                        <Icon name="trash-2" size={15} />
                      </IconButton>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {confirmId && (
        <div className="modal-backdrop" onClick={() => setConfirmId(null)}>
          <div className="modal" style={{ width: 380 }} onClick={(e) => e.stopPropagation()}>
            <div className="modal__head"><Icon name="trash-2" size={18} color="var(--danger-500)" /><h3>Delete workout?</h3></div>
            <p className="modal__sub">This removes the session and its sets. This can't be undone.</p>
            <div className="modal__actions">
              <Button variant="outline" onClick={() => setConfirmId(null)}>Cancel</Button>
              <Button variant="destructive" onClick={() => { onDelete(confirmId); setConfirmId(null); }}
                iconStart={<Icon name="trash-2" size={14} color="#fff" />}>Delete</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

window.WorkoutsScreen = WorkoutsScreen;
