/* ============================================================
   Auth — Login + Register (loading / error / success states).
   ============================================================ */
function AuthShell({ title, sub, children, foot, accent }) {
  return (
    <div className="auth" data-accent={accent}>
      <div className="auth__card">
        <div className="auth__brand">
          <img src="assets/logo-mascot.png" alt="" />
          <b>Workout<span> Wiz</span></b>
        </div>
        <h2>{title}</h2>
        <p className="sub">{sub}</p>
        {children}
        <div className="auth__foot">{foot}</div>
      </div>
    </div>
  );
}

function LoginScreen({ onLogin, goRegister, accent }) {
  const [email, setEmail] = React.useState("morgan@gym.com");
  const [pw, setPw] = React.useState("trainsmart");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  function submit(e) {
    e.preventDefault();
    setError("");
    if (!email.trim() || !pw.trim()) { setError("Enter your email and password to continue."); return; }
    setLoading(true);
    setTimeout(() => {
      if (pw === "wrong") { setLoading(false); setError("Incorrect email or password. Please try again."); return; }
      onLogin({ email });
    }, 900);
  }

  return (
    <AuthShell accent={accent} title="Sign in" sub="Your AI strength coach is ready."
      foot={<span>Need an account? <a onClick={goRegister}>Register</a></span>}>
      {error && <div className="alert" style={{ marginBottom: 16 }}><Icon name="alert-circle" size={16} />{error}</div>}
      <form onSubmit={submit}>
        <Field label="Email" htmlFor="le">
          <Input id="le" type="email" value={email} disabled={loading}
            onChange={(e) => setEmail(e.target.value)} icon={<Icon name="mail" size={16} />} />
        </Field>
        <Field label="Password" htmlFor="lp">
          <Input id="lp" type="password" value={pw} disabled={loading}
            onChange={(e) => setPw(e.target.value)} icon={<Icon name="lock" size={16} />} />
        </Field>
        <Button type="submit" variant="gradient" size="lg" block disabled={loading}
          iconStart={loading ? <Icon name="loader-circle" size={16} color="#fff" style={{ animation: "spin 0.8s linear infinite" }} /> : null}>
          {loading ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthShell>
  );
}

function RegisterScreen({ onRegister, goLogin, accent }) {
  const [email, setEmail] = React.useState("");
  const [pw, setPw] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  function submit(e) {
    e.preventDefault();
    setError("");
    if (!email.trim() || !pw.trim()) { setError("Email and password are required."); return; }
    if (!/^[^@]+@[^@]+\.[^@]+$/.test(email)) { setError("Enter a valid email address."); return; }
    if (pw.length < 6) { setError("Password must be at least 6 characters."); return; }
    setLoading(true);
    setTimeout(() => onRegister({ email }), 1000);
  }

  return (
    <AuthShell accent={accent} title="Create account" sub="Start training smarter, not harder."
      foot={<span>Already have an account? <a onClick={goLogin}>Sign in</a></span>}>
      {error && <div className="alert" style={{ marginBottom: 16 }}><Icon name="alert-circle" size={16} />{error}</div>}
      <form onSubmit={submit}>
        <Field label="Email" htmlFor="re">
          <Input id="re" type="email" value={email} disabled={loading} placeholder="you@example.com"
            onChange={(e) => setEmail(e.target.value)} icon={<Icon name="mail" size={16} />} />
        </Field>
        <Field label="Password" htmlFor="rp" hint="At least 6 characters.">
          <Input id="rp" type="password" value={pw} disabled={loading} placeholder="Create a password"
            onChange={(e) => setPw(e.target.value)} icon={<Icon name="lock" size={16} />} />
        </Field>
        <Button type="submit" variant="gradient" size="lg" block disabled={loading}
          iconStart={loading ? <Icon name="loader-circle" size={16} color="#fff" style={{ animation: "spin 0.8s linear infinite" }} /> : null}>
          {loading ? "Creating account…" : "Create account"}
        </Button>
      </form>
    </AuthShell>
  );
}

window.LoginScreen = LoginScreen;
window.RegisterScreen = RegisterScreen;
