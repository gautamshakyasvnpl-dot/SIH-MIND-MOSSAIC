import { useState } from "react";
import { Link } from "react-router-dom";
import { postCommunication } from "../lib/api";
import { usePageTitle } from "../hooks/usePageTitle";

type Mode = "email" | "structure" | "presentation";

const TABS: [Mode, string][] = [
  ["email", "Email assistant"],
  ["structure", "Message structurer"],
  ["presentation", "Presentation outline"],
];

export default function Communicate() {
  usePageTitle("Communication assistant");
  const [mode, setMode] = useState<Mode>("email");
  const [raw, setRaw] = useState("");
  const [recipient, setRecipient] = useState("");
  const [deadline, setDeadline] = useState("");
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setBusy(true);
    setError("");
    try {
      const res = await postCommunication({ mode, raw, recipient, deadline, topic });
      const r = res.result;
      if (typeof r === "string") setResult(r);
      else if ("key_points" in r)
        setResult(
          `OPENING\n${r.opening}\n\nKEY POINTS\n${r.key_points.map((k, i) => `${i + 1}. ${k}`).join("\n")}\n\nCONCLUSION\n${r.conclusion}\n\nSPEAKER NOTES\n- ${r.speaker_notes.join("\n- ")}`
        );
      else
        setResult(
          `SITUATION\n${r.situation}\n\nEXPLANATION\n${r.explanation}\n\nREQUEST\n${r.request}\n\nDEADLINE\n${r.deadline}`
        );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not draft right now.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>Communication assistant</h1>
      <p>
        Turn rough thoughts into clear drafts. Templates are deterministic and
        labelled as such — nothing pretends to be magic. Need viva practice?{" "}
        <Link to="/library">Open a document's viva studio →</Link>
      </p>

      <ul className="mood-row" role="tablist" aria-label="Assistant modes">
        {TABS.map(([m, label]) => (
          <li key={m} role="presentation">
            <button
              type="button"
              role="tab"
              aria-selected={mode === m}
              onClick={() => {
                setMode(m);
                setResult("");
              }}
            >
              {label}
            </button>
          </li>
        ))}
      </ul>

      {mode === "presentation" ? (
        <>
          <p>
            <label htmlFor="topic">Presentation topic</label>
            <br />
            <input
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              style={{ width: "min(28rem, 100%)" }}
            />
          </p>
          <p>
            <label htmlFor="notes">Rough notes (optional)</label>
            <br />
            <textarea id="notes" rows={4} value={raw} onChange={(e) => setRaw(e.target.value)} style={{ width: "min(28rem, 100%)" }} />
          </p>
        </>
      ) : (
        <>
          <p>
            <label htmlFor="raw">{mode === "email" ? "What do you need to say?" : "Your rough message"}</label>
            <br />
            <textarea id="raw" rows={4} value={raw} onChange={(e) => setRaw(e.target.value)} style={{ width: "min(28rem, 100%)" }} />
          </p>
          {mode === "email" && (
            <>
              <p>
                <label htmlFor="who">To (name/title)</label>
                <br />
                <input id="who" value={recipient} onChange={(e) => setRecipient(e.target.value)} style={{ width: "min(28rem, 100%)" }} />
              </p>
              <p>
                <label htmlFor="when">Deadline to propose (optional)</label>
                <br />
                <input id="when" value={deadline} onChange={(e) => setDeadline(e.target.value)} style={{ width: "min(28rem, 100%)" }} />
              </p>
            </>
          )}
        </>
      )}

      <button type="submit" onClick={() => void run()} disabled={busy || (!raw.trim() && !topic.trim())}>
        {busy ? "Drafting…" : "Draft it"}
      </button>

      {error && <p role="alert">{error}</p>}
      {result && (
        <section aria-labelledby="draft-heading">
          <h2 id="draft-heading">Your draft</h2>
          <pre className="card prose" style={{ whiteSpace: "pre-wrap" }}>{result}</pre>
        </section>
      )}
    </main>
  );
}
