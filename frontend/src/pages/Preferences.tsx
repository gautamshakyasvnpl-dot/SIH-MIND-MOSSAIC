import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  deleteAccount,
  deleteHistory,
  downloadExport,
  getMemory,
  getPreferences,
  putPreferences,
  type MemoryOut,
  type ScoresOut,
} from "../lib/api";
import ConsentSection from "../components/ConsentSection";
import { useSensorySettings } from "../context/SensorySettings";
import { useProfileSync } from "../hooks/useProfileSync";
import { usePageTitle } from "../hooks/usePageTitle";

const EVENT_WORDS: Record<string, string> = {
  feedback_too_long: "said an explanation was too long",
  requested_simpler: "asked for simpler wording",
  explain_deeper_stepwise: "asked to go deeper",
  requested_example: "requested an example",
  feedback_need_example: "asked for an example",
  opened_concept_map: "opened a concept map",
  read_aloud: "used read-aloud",
  played_audio: "played audio",
  quiz_started: "started a practice quiz",
  quiz_correct: "answered a quiz item correctly",
  quiz_incorrect: "missed a quiz item",
  thumbs_up: "marked something helpful",
  thumbs_down: "marked something unhelpful",
  completed_card: "finished a concept card",
};

export default function PersonalizationCenter() {
  const [prefs, setPrefs] = useState<ScoresOut | null>(null);
  const [draft, setDraft] = useState<Record<string, number>>({});
  const [memory, setMemory] = useState<MemoryOut | null>(null);
  const [msg, setMsg] = useState("");
  const [exportMsg, setExportMsg] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const { prefs: sensory, update: updateSensory } = useSensorySettings();
  const syncProfile = useProfileSync();
  const navigate = useNavigate();

  usePageTitle("Personalization center");

  const refreshAll = () => {
    void getPreferences()
      .then((p) => {
        setPrefs(p);
        setDraft({ ...p.scores });
      })
      .catch(() => setMsg("Could not load your preferences."));
    void getMemory().then(setMemory).catch(() => setMemory(null));
  };

  useEffect(refreshAll, []);

  async function clearHistory() {
    if (!confirm("Delete all recorded interactions and reset preference scores to neutral?")) return;
    try {
      await deleteHistory();
      setMsg("Interaction history deleted and scores reset.");
      refreshAll();
    } catch {
      setMsg("Could not delete history right now.");
    }
  }

  async function save() {
    try {
      const res = await putPreferences(draft);
      setPrefs(res);
      setMsg("Saved — the reader adapts from these scores immediately.");
      void syncProfile();
    } catch {
      setMsg("Could not save right now.");
    }
  }

  async function exportData() {
    setExportMsg("Preparing your export…");
    try {
      await downloadExport();
      setExportMsg("Export downloaded as neurolearn-export.json.");
    } catch {
      setExportMsg("Could not prepare the export right now.");
    }
  }

  async function wipeAccount() {
    if (!confirmDelete) return;
    setDeleting(true);
    try {
      await deleteAccount();
      localStorage.removeItem("sahaik_token");
      navigate("/landing");
    } catch {
      setDeleting(false);
      setConfirmDelete(false);
      setMsg("Could not delete the account right now — nothing was changed.");
    }
  }

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>Personalization center</h1>
      <p className="prose">
        How NEUROLEARN understands your learning preferences. These are
        <strong> learning-preference scores</strong>, updated by your actions —
        never diagnoses. Every value below is yours to change.
      </p>

      {prefs === null ? (
        <p role="status">{msg || "Loading…"}</p>
      ) : (
        <>
          <section aria-labelledby="scores-heading">
            <h2 id="scores-heading">Preference scores</h2>
            {Object.entries(prefs.scores).map(([key, value]) => (
              <p key={key}>
                <label htmlFor={`score-${key}`}>
                  {prefs.labels[key] ?? key} — {Math.round(value * 100)}%
                </label>
                <br />
                <input
                  id={`score-${key}`}
                  type="range"
                  min={0}
                  max={100}
                  value={Math.round((draft[key] ?? value) * 100)}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, [key]: Number(e.target.value) / 100 }))
                  }
                  style={{ width: "min(24rem, 100%)" }}
                />
              </p>
            ))}
            <button type="button" onClick={() => void save()}>Save preferences</button>{" "}
            <button
              type="button"
              onClick={() => setDraft({ ...prefs.scores })}
            >
              Reset changes
            </button>
          </section>

          {msg && <p role="status" aria-live="polite">{msg}</p>}

          <section aria-labelledby="why-heading">
            <h2 id="why-heading">Why the reader looks like this</h2>
            <ul className="prose">
              {(prefs.profile_lines.length
                ? prefs.profile_lines
                : ["No strong signals yet — interact with a reader card first."]
              ).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </section>

          <section aria-labelledby="appearance-heading">
            <h2 id="appearance-heading">Appearance &amp; comfort</h2>
            <p>
              <label htmlFor="tsize">Text size</label>{" "}
              <select
                id="tsize"
                value={sensory.text_size}
                onChange={(e) => updateSensory({ text_size: e.target.value as "normal" | "large" })}
              >
                <option value="normal">Normal</option>
                <option value="large">Large</option>
              </select>
            </p>
            <p>
              <label>
                <input
                  type="checkbox"
                  checked={sensory.high_contrast}
                  onChange={(e) => updateSensory({ high_contrast: e.target.checked })}
                />{" "}
                High contrast mode
              </label>
            </p>
            <p>
              <label>
                <input
                  type="checkbox"
                  checked={sensory.reduce_motion}
                  onChange={(e) => updateSensory({ reduce_motion: e.target.checked })}
                />{" "}
                Reduce motion and animation
              </label>
            </p>
          </section>

          <section aria-labelledby="memory-heading">
            <h2 id="memory-heading">Personal learning memory</h2>
            {memory && memory.struggled_concepts.length > 0 ? (
              <>
                <ul className="review-table">
                  {memory.struggled_concepts.map((c) => (
                    <li key={c.concept}>
                      <span>{c.concept}</span>
                      <strong>{c.misses} miss{c.misses > 1 ? "es" : ""}</strong>
                    </li>
                  ))}
                </ul>
                <ul className="prose">
                  {memory.suggestions.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p>No tricky concepts recorded yet — quiz results will appear here.</p>
            )}
          </section>

          <section aria-labelledby="history-heading">
            <h2 id="history-heading">Recent adaptations (latest 12)</h2>
            {prefs.recent_events.length === 0 ? (
              <p>No interactions recorded yet.</p>
            ) : (
              <ul className="review-table">
                {prefs.recent_events.map((e) => (
                  <li key={e.id}>
                    <span>{EVENT_WORDS[e.event] ?? e.event}</span>
                    <span>{new Date(e.created_at).toLocaleString()}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section aria-labelledby="data-heading">
            <h2 id="data-heading">Data controls</h2>
            <p>
              <button type="button" onClick={() => void exportData()}>
                Export my data (JSON)
              </button>{" "}
              <button type="button" onClick={() => void clearHistory()}>
                Delete interaction history
              </button>
            </p>
            {exportMsg && (
              <p role="status" aria-live="polite">
                {exportMsg}
              </p>
            )}
            {!confirmDelete ? (
              <p>
                <button type="button" onClick={() => setConfirmDelete(true)}>
                  Delete my account and all data
                </button>
              </p>
            ) : (
              <div role="alert">
                <p>
                  This permanently deletes your account and everything stored
                  with it: profile, consents, documents and their extracted
                  text, adaptations, audio files, tasks and sprints, viva
                  sessions, check-ins, interaction events and preference
                  scores. This cannot be undone.
                </p>
                <button type="button" disabled={deleting} onClick={() => void wipeAccount()}>
                  {deleting ? "Deleting…" : "Yes, delete everything"}
                </button>{" "}
                <button type="button" disabled={deleting} onClick={() => setConfirmDelete(false)}>
                  Cancel
                </button>
              </div>
            )}
            <p>
              <small>
                Your documents, adaptations, tasks, viva sessions and check-ins
                are stored on the server with your account. The export above
                contains a copy of all of it. Wellbeing support is at the{" "}
                <Link to="/wellbeing">wellbeing hub</Link>.
              </small>
            </p>
          </section>

          <ConsentSection heading="Your consent choices" />
        </>
      )}
    </main>
  );
}
