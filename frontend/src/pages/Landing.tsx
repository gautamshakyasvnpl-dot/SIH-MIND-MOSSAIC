import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login, setToken } from "../lib/api";
import { PRODUCT_NAME, PRODUCT_SUBTITLE } from "../lib/brand";
import { useProfileSync } from "../hooks/useProfileSync";
import { usePageTitle } from "../hooks/usePageTitle";

const LAYERS = [
  {
    name: "LEARN",
    text: "Upload lecture slides, PDFs or notes — we turn dense material into structured concept cards.",
  },
  {
    name: "ADAPT",
    text: "Explanations change length, depth and format based on your learning preferences and feedback.",
  },
  {
    name: "SUPPORT",
    text: "AI tutor, practice vivas, focus mode, task sprints and wellbeing check-ins — always optional.",
  },
  {
    name: "IMPROVE",
    text: "Every interaction updates your preference profile. You can see and edit exactly what we learned.",
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const syncProfile = useProfileSync();
  const [demoMsg, setDemoMsg] = useState("");
  const [demoBusy, setDemoBusy] = useState(false);

  usePageTitle("Welcome");

  async function tryDemo() {
    setDemoBusy(true);
    setDemoMsg("");
    try {
      const res = await login("demo@neurolearn.app", "demo12345");
      setToken(res.token);
      void syncProfile();
      navigate("/dashboard");
    } catch {
      setDemoMsg(
        "Demo account not found on this server. Run: backend\\.venv\\Scripts\\python backend\\scripts\\seed_demo.py"
      );
    } finally {
      setDemoBusy(false);
    }
  }

  return (
    <main id="main" tabIndex={-1} className="landing">
      <section className="auth-brand">
        <p className="wordmark">
          <span className="mark" aria-hidden="true">स</span>
          <span>
            NEURO<span className="tilde">LEARN</span>
          </span>
        </p>
        <p className="auth-tag">{PRODUCT_SUBTITLE}</p>
      </section>

      <section aria-labelledby="hero-heading">
        <h1 className="page-title" id="hero-heading" tabIndex={-1}>
          This is not another chatbot.
        </h1>
        <p className="prose">
          Dense lectures, timed labs, noisy classrooms and viva nerves hit
          neurodivergent students hardest. {PRODUCT_NAME} reshapes the same
          material around <strong>how you learn</strong> — and shows you why it
          changed.
        </p>
      </section>

      <section aria-labelledby="layers-heading">
        <h2 id="layers-heading">One platform, four layers</h2>
        <ul className="layer-grid">
          {LAYERS.map((l) => (
            <li key={l.name}>
              <h3>{l.name}</h3>
              <p><small>{l.text}</small></p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="privacy-heading">
        <h2 id="privacy-heading">Preferences, not diagnoses</h2>
        <p className="prose">
          <small>
            We never diagnose. There is no “what disorder do you have?” question — only
            “what helps you learn?”. Every adaptation is explainable, every score is
            editable, and your data stays yours. Wellbeing support is practical, with a
            clear line to human counselling when things feel heavy.
          </small>
        </p>
      </section>

      <section aria-labelledby="cta-heading">
        <h2 id="cta-heading">Try it in two minutes</h2>
        <p className="cta-row">
          <Link
            to="/register"
            className="button-hero"
            style={{
              display: "inline-block",
              borderRadius: "var(--radius-pill)",
              padding: "calc(var(--space-unit) * 1.35) calc(var(--space-unit) * 3)",
              fontWeight: 700,
              textDecoration: "none",
              boxShadow: "var(--shadow-card)",
            }}
          >
            Create free account
          </Link>{" "}
          <button type="button" disabled={demoBusy} onClick={() => void tryDemo()}>
            {demoBusy ? "Loading demo…" : "Try the demo →"}
          </button>
        </p>
        {demoMsg && (
          <p role="alert">
            <small>{demoMsg}</small>
          </p>
        )}
        <p>
          <small>
            Judges: run <code>backend\.venv\Scripts\python backend\scripts\seed_demo.py</code>{" "}
            then sign in as <code>demo@neurolearn.app</code> / <code>demo12345</code>.
          </small>
        </p>
      </section>
    </main>
  );
}
