/* ============================================================
   App shell — top navigation bar (responsive).
   ============================================================ */
function TopNav({ route, navigate, units, setUnits, onLogout }) {
  const [menuOpen, setMenuOpen] = React.useState(false);
  const links = [
    { id: "chat", label: "Chat", icon: "sparkles" },
    { id: "workouts", label: "Workouts", icon: "calendar-days" },
    { id: "exercises", label: "Exercises", icon: "list" },
  ];
  const isActive = (id) =>
    route === id || (id === "workouts" && (route === "workouts/new" || route.startsWith("workout/")));

  const go = (r) => { setMenuOpen(false); navigate(r); };

  return (
    <React.Fragment>
      <header className="topnav">
        <a className="topnav__brand" href="#chat" onClick={(e) => { e.preventDefault(); go("chat"); }}>
          <img src="assets/logo-mascot.png" alt="" />
          <b>Workout<span> Wiz</span></b>
        </a>

        <nav className="topnav__links">
          {links.map((l) => (
            <button key={l.id} className="navlink" data-active={isActive(l.id)} onClick={() => go(l.id)}>
              <Icon name={l.icon} size={16} /> {l.label}
            </button>
          ))}
        </nav>

        <div className="topnav__spacer" />

        <div className="topnav__right">
          <div className="unit-toggle">
            <span className="lbl">Units</span>
            <Tabs value={units} onChange={setUnits} size="sm"
              items={[{ value: "kg", label: "kg" }, { value: "lb", label: "lb" }]} />
          </div>
          <Button variant="gradient" size="sm" onClick={() => go("workouts/new")}
            iconStart={<Icon name="plus" size={15} color="#fff" />}>
            Start New Workout
          </Button>
          <div className="topnav__user">
            <Avatar name="Morgan Vale" size="sm" />
          </div>
          <IconButton aria-label="Log out" variant="ghost" size="sm" onClick={onLogout}>
            <Icon name="log-out" size={16} />
          </IconButton>
          <IconButton aria-label="Menu" variant="ghost" size="sm" className="nav-burger"
            onClick={() => setMenuOpen((v) => !v)}>
            <Icon name={menuOpen ? "x" : "menu"} size={18} />
          </IconButton>
        </div>
      </header>

      <div className={"nav-drawer" + (menuOpen ? " open" : "")}>
        <div style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: 4, borderBottom: "1px solid var(--border)", background: "var(--surface-card)" }}>
          {links.map((l) => (
            <button key={l.id} className="navlink" data-active={isActive(l.id)} onClick={() => go(l.id)}>
              <Icon name={l.icon} size={16} /> {l.label}
            </button>
          ))}
          <button className="navlink" onClick={() => go("workouts/new")}>
            <Icon name="plus-circle" size={16} /> Start New Workout
          </button>
        </div>
      </div>
    </React.Fragment>
  );
}

function Shell({ route, navigate, units, setUnits, onLogout, children }) {
  return (
    <div className="shell">
      <TopNav route={route} navigate={navigate} units={units} setUnits={setUnits} onLogout={onLogout} />
      <div className="view ww-scroll">{children}</div>
    </div>
  );
}

window.Shell = Shell;
window.TopNav = TopNav;
