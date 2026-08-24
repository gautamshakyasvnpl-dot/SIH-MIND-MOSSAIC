import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createCheckin,
  getAnalytics,
  getPreferences,
  listDocuments,
  listTasks,
  type AnalyticsOut,
  type DocumentMeta,
  type ScoresOut,
  type Task,
} from "../lib/api";
import { suggestForMood } from "../lib/mood";
import { usePageTitle } from "../hooks/usePageTitle";

const MOODS: [number, string][] = [
  [4, "🙂 Good"],
  [3, "😐 Okay"],
  [2, "😟 Overwhelmed"],
];

export default function Dashboard() {
  const [docs, setDocs] = useState<DocumentMeta[] | null>(null);
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [prefs, setPrefs] = useState<ScoresOut | null>(null);
  const [stats, setStats] = useState<AnalyticsOut | null>(null);
  const [moodMsg, setMoodMsg] = useState("");
  const [posting, setPosting] = useState(false);
  const latest = docs?.[0];
  const openTasks = tasks?.filter((t) => t.status !== "done") ?? [];

  usePageTitle("Dashboard");

  useEffect(() => {
    void listDocuments().then((r) => setDocs(r.items)).catch(() => setDocs([]));
    void listTasks().then((r) => setTasks(r.items)).catch(() => setTasks([]));
    void getPreferences().then(setPrefs).catch(() => setPrefs(null));
    void getAnalytics().then(setStats).catch(() => setStats(null));
  }, []);

  async function quickCheckin(mood: number) {
    if (posting) return;
    setPosting(true);
    try {
      const res = await createCheckin(mood, null);
      setMoodMsg(res.suggestion);
    } catch {
      setMoodMsg("Could not save the check-in — the Wellbeing page has the full flow.");
    } finally {
      setPosting(false);
    }
  }

  const strongPrefs = Object.entries(prefs?.scores ?? {})
    .filter(([, v]) => v >= 0.62)
    .map(([k]) => prefs?.labels[k] ?? k);

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>Today at a glance</h1>

      <section aria-labelledby="impact-heading">
        <h2 id="impact-heading">Your impact so far</h2>
        {stats === null ? (
          <p><small>Loading stats…</small></p>
        ) : (
          <ul className="review-table">
            <li><span>Adaptive changes recorded</span><strong>{stats.adaptive_changes_total}</strong></li>
            <li><span>…in the last 24 hours</span><strong>{stats.adaptive_changes_last_24h}</strong></li>
            <li><span>Practice quiz answers</span><strong>{stats.quiz_correct} correct · {stats.quiz_incorrect} missed</strong></li>
            <li><span>Documents in library</span><strong>{stats.documents_count}</strong></li>
          </ul>
        )}
      </section>

      <section aria-labelledby="continue-heading">
        <h2 id="continue-heading">Continue learning</h2>
        {docs === null ? (
          <p>Loading…</p>
        ) : !latest ? (
          <p>
            No material yet.{" "}
            <Link to="/library">Upload your first lecture →</Link>
          </p>
        ) : (
          <p>
            <Link to={`/document/${latest.id}/reader`}>
              {latest.filename} — open adaptive reader →
            </Link>
          </p>
        )}
      </section>

      <section aria-labelledby="plan-heading">
        <h2 id="plan-heading">Today's learning plan</h2>
        {tasks === null ? (
          <p>Loading…</p>
        ) : openTasks.length === 0 ? (
          <p>Nothing planned. Add a task on the sprint board and it will be broken into sprints.</p>
        ) : (
          <ul>
            {openTasks.slice(0, 4).map((t) => (
              <li key={t.id}>
                {t.title} — {t.sprints.filter((s) => !s.done).length} sprints left
              </li>
            ))}
          </ul>
        )}
        <p>
          <Link to="/tasks">Open sprint board →</Link>
        </p>
      </section>

      <section aria-labelledby="profile-heading">
        <h2 id="profile-heading">Your learning profile right now</h2>
        {strongPrefs.length ? (
          <ul className="layer-grid">
            {strongPrefs.map((p) => (
              <li key={p}><p>{p}</p></li>
            ))}
          </ul>
        ) : (
          <p>
            <small>
              Not enough signals yet — use the reader for a bit and this fills up.
              See the{" "}
              <Link to="/preferences">personalization center</Link>.
            </small>
          </p>
        )}
      </section>

      <section aria-labelledby="wellbeing-heading">
        <h2 id="wellbeing-heading">How is studying going?</h2>
        <p><small>Optional self-report. Saved with your account; exportable from Preferences.</small></p>
        <ul className="mood-row">
          {MOODS.map(([m, label]) => (
            <li key={m}>
              <button type="button" disabled={posting} onClick={() => void quickCheckin(m)}>{label}</button>
            </li>
          ))}
        </ul>
        {moodMsg && (
          <p role="status" aria-live="polite" className="prose">
            {suggestForMood(moodMsg)}
          </p>
        )}
      </section>

      <section aria-labelledby="actions-heading">
        <h2 id="actions-heading">Quick actions</h2>
        <ul className="layer-grid">
          <li><Link to="/library"><p>Upload material</p></Link></li>
          <li><Link to={`/document/${latest?.id ?? ""}/reader`}><p>Adaptive reader</p></Link></li>
          <li><Link to={latest ? `/focus/${latest.id}` : "/library"}><p>Focus mode</p></Link></li>
          <li><Link to={latest ? `/document/${latest.id}/viva` : "/library"}><p>Practice viva</p></Link></li>
          <li><Link to="/communicate"><p>Communication assistant</p></Link></li>
          <li><Link to="/preferences"><p>Personalization center</p></Link></li>
        </ul>
      </section>
    </main>
  );
}
