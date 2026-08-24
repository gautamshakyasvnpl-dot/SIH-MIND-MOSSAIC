import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  createTask,
  deleteTask,
  listTasks,
  toggleSprint,
  type Task,
} from "../lib/api";
import { usePageTitle } from "../hooks/usePageTitle";

export default function SprintBoard() {
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [title, setTitle] = useState("");
  const [due, setDue] = useState("");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState("");
  const [validation, setValidation] = useState("");
  const [busy, setBusy] = useState(false);

  usePageTitle("Sprint board");

  const refresh = useCallback(async () => {
    try {
      const res = await listTasks();
      setTasks(res.items);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not load tasks");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim()) {
      setValidation("Please describe what you need to do — even a few words is enough.");
      return;
    }
    setValidation("");
    setBusy(true);
    setStatus("Planning your sprints…");
    try {
      await createTask(title.trim(), due || null, notes.trim() || null);
      setTitle("");
      setDue("");
      setNotes("");
      setStatus("Task created with sprint plan.");
      await refresh();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not create task");
    } finally {
      setBusy(false);
    }
  }

  async function onToggle(taskId: string, sprintId: string) {
    try {
      await toggleSprint(taskId, sprintId);
      await refresh();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Toggle failed");
    }
  }

  async function onDelete(taskId: string) {
    try {
      await deleteTask(taskId);
      await refresh();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>Sprint board</h1>
      <section aria-labelledby="new-task-heading">
        <h2 id="new-task-heading">New task</h2>
        <form onSubmit={(e) => void onCreate(e)} noValidate>
          <p>
            <label htmlFor="title">What do you need to do?</label>
            <br />
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (validation) setValidation("");
              }}
              style={{ width: "min(28rem, 100%)" }}
            />
          </p>
          <p>
            <label htmlFor="due">Due date (optional)</label>
            <br />
            <input
              id="due"
              type="date"
              value={due}
              onChange={(e) => setDue(e.target.value)}
            />
          </p>
          <p>
            <label htmlFor="notes">Notes (optional)</label>
            <br />
            <textarea
              id="notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{ width: "min(28rem, 100%)" }}
            />
          </p>
          {validation && (
            <p role="status" aria-live="polite" className="emotion-note">
              {validation}
            </p>
          )}
          <button type="submit" disabled={busy}>
            {busy ? "Planning…" : "Break it into sprints"}
          </button>
        </form>
      </section>
      <p role="status" aria-live="polite">
        {status}
      </p>
      <section aria-labelledby="board-heading">
        <h2 id="board-heading">Your tasks</h2>
        {tasks === null ? (
          <p>Loading…</p>
        ) : tasks.length === 0 ? (
          <p>No tasks yet. Add one above and SahAIk will plan the sprints.</p>
        ) : (
          tasks.map((t) => (
            <article key={t.id} className="task-card">
              <h3>
                {t.title}{" "}
                <span className="stamp">
                  {t.status === "done" ? "done" : `${t.sprints.filter((s) => !s.done).length} left`}
                </span>
              </h3>
              {t.due_date && (
                <p>
                  <small>Due {t.due_date}</small>
                </p>
              )}
              <ul className="sprint-list">
                {t.sprints.map((s) => (
                  <li key={s.id}>
                    <label>
                      <input
                        type="checkbox"
                        checked={s.done}
                        onChange={() => onToggle(t.id, s.id)}
                      />{" "}
                      <span>
                        {s.description} <small>({s.minutes} min)</small>
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
              <button type="button" onClick={() => onDelete(t.id)}>
                Delete task
              </button>
            </article>
          ))
        )}
      </section>
    </main>
  );
}
