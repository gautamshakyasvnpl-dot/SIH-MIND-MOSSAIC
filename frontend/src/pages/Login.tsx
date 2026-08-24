import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getProfile, login, setToken } from "../lib/api";
import { useSensorySettings } from "../context/SensorySettings";
import { profileToSensoryPatch } from "../lib/profileSync";
import { usePageTitle } from "../hooks/usePageTitle";

export default function Login() {
  const navigate = useNavigate();
  const { prefs: sensory, update: updateSensory } = useSensorySettings();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  usePageTitle("Sign in");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await login(email, password);
      setToken(res.token);
      const profile = await getProfile();
      const patch = profileToSensoryPatch(profile, sensory);
      if (patch) updateSensory(patch);
      navigate(profile.onboarding_complete ? "/library" : "/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
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
      <h1 className="page-title" tabIndex={-1}>Sign in</h1>
      <form onSubmit={ onSubmit}>
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
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </p>
        {error && <p role="alert" aria-live="polite">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p>
        New here? <Link to="/register">Create an account</Link>
      </p>
    </main>
  );
}
