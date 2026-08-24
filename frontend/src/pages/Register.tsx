import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register, setToken } from "../lib/api";
import { useProfileSync } from "../hooks/useProfileSync";
import { usePageTitle } from "../hooks/usePageTitle";

export default function Register() {
  const navigate = useNavigate();
  const syncProfile = useProfileSync();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  usePageTitle("Create your account");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await register(email, password, displayName);
      setToken(res.token);
      await syncProfile();
      navigate("/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main id="main" tabIndex={-1} className="auth-wrap">
      <div className="auth-brand">
        <p className="wordmark">
          <span className="mark" aria-hidden="true">स</span>
          <span>
            Sah<span className="tilde">AI</span>k
          </span>
        </p>
        <p className="auth-tag">learning, at your pace — not the other way round</p>
      </div>
      <h1 className="page-title" tabIndex={-1}>Create your account</h1>
      <form onSubmit={ onSubmit}>
        <p>
          <label htmlFor="displayName">Display name</label>
          <br />
          <input
            id="displayName"
            type="text"
            required
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            autoComplete="name"
          />
        </p>
        <p>
          <label htmlFor="email">Email</label>
          <br />
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
        </p>
        <p>
          <label htmlFor="password">Password</label>
          <br />
          <input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
          />
        </p>
        {error && <p role="alert" aria-live="polite">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Creating…" : "Create account"}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </main>
  );
}
