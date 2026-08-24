import { useCallback, useEffect, useState } from "react";
import {
  createCheckin,
  listCheckins,
  type Checkin,
} from "../lib/api";
import { usePageTitle } from "../hooks/usePageTitle";

const MOOD_LABELS: Record<number, string> = {
  1: "Really struggling",
  2: "Low",
  3: "Okay",
  4: "Good",
  5: "Great",
};

export default function Wellbeing() {
  usePageTitle("Wellbeing");
  const [history, setHistory] = useState<Checkin[] | null>(null);
  const [latest, setLatest] = useState<Checkin | null>(null);
  const [note, setNote] = useState("");
  const [status, setStatus] = useState("");
  const [posting, setPosting] = useState(false);
  const [breathing, setBreathing] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await listCheckins();
      setHistory(res.items);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not load check-ins");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onCheckin(mood: number) {
    if (posting) return;
    setPosting(true);
    setStatus("Saving…");
    try {
      const res = await createCheckin(mood, note.trim() || null);
      setLatest(res);
      setNote("");
      setStatus("Check-in saved.");
      await refresh();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not save");
    } finally {
      setPosting(false);
    }
  }

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>How are you doing today?</h1>
      <p>
        A quick self-report check-in — you describe your day, no cameras or
        sensors involved. Your mood and note are stored on the server with
        your account so your history follows you; export them from
        Preferences → Data controls anytime.
      </p>
      <fieldset>
        <legend>Pick the closest match</legend>
        {([1, 2, 3, 4, 5] as const).map((m) => (
          <p key={m}>
            <button type="button" disabled={posting} onClick={() => onCheckin(m)}>
              {posting ? "Saving…" : MOOD_LABELS[m]}
            </button>
          </p>
        ))}
      </fieldset>
      <p>
        <label htmlFor="note">Add a note (optional)</label>
        <br />
        <textarea
          id="note"
          rows={2}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          style={{ width: "min(28rem, 100%)" }}
        />
      </p>
      <p role="status" aria-live="polite">
        {status}
      </p>
      {latest && (
        <section aria-labelledby="suggestion-heading">
          <h2 id="suggestion-heading">A suggestion for you</h2>
          <article className="prose">
            <p>{latest.suggestion}</p>
          </article>
          {latest.mood <= 2 && (
            <div>
              <button type="button" onClick={() => setBreathing(!breathing)}>
                {breathing ? "Hide" : "Show"} box breathing steps
              </button>
              <div
                className="breath-circle"
                role="img"
                aria-label="Breathing pace circle: expands as you breathe in, shrinks as you breathe out"
              />
            </div>
          )}
          {breathing && (
            <ol>
              <li>Breathe in through your nose — 4 seconds.</li>
              <li>Hold — 4 seconds.</li>
              <li>Breathe out slowly — 4 seconds.</li>
              <li>Hold — 4 seconds. Repeat four rounds.</li>
            </ol>
          )}
          <p>
            <small>
              Need more support? The university Equal Opportunity Cell and
              student counselling services can help. Reaching out is a strong
              move.
            </small>
          </p>
        </section>
      )}
      <section aria-labelledby="history-heading">
        <h2 id="history-heading">Recent check-ins</h2>
        {history === null ? (
          <p>Loading…</p>
        ) : history.length === 0 ? (
          <p>No check-ins yet.</p>
        ) : (
          <ul>
            {history.map((c) => (
              <li key={c.id}>
                {new Date(c.created_at).toLocaleString()} — {MOOD_LABELS[c.mood]}
                {c.note ? ` (${c.note})` : ""}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
