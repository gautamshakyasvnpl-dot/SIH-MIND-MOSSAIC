import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReader, listDocuments } from "../lib/api";
import { usePageTitle } from "../hooks/usePageTitle";

const DURATIONS = [25, 45, 60];

export default function FocusMode() {
  const { id } = useParams();
  usePageTitle("Focus mode");
  const [docs, setDocs] = useState<{ id: string; filename: string }[] | null>(null);
  const [selectedDoc, setSelectedDoc] = useState(id ?? "");
  const [minutes, setMinutes] = useState(25);
  const [custom, setCustom] = useState("");
  const [cards, setCards] = useState<string[] | null>(null);
  const [cardIndex, setCardIndex] = useState(0);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);

  useEffect(() => {
    if (id) return;
    void listDocuments()
      .then((r) => setDocs(r.items))
      .catch(() => setDocs([]));
  }, [id]);

  useEffect(() => {
    if (secondsLeft === null) return;
    if (secondsLeft <= 0) return;
    const t = setTimeout(() => setSecondsLeft((s) => (s ?? 1) - 1), 1000);
    return () => clearTimeout(t);
  }, [secondsLeft]);

  async function begin() {
    const docId = id ?? selectedDoc;
    if (!docId) return;
    try {
      const r = await getReader(docId);
      setCards(r.cards.map((c) => `${c.title}. ${c.simple}`));
      setCardIndex(0);
    } catch {
      setCards(["Could not load this document — check it in the library first."]);
    }
  }

  const total = useMemo(
    () => cards?.length ?? 0,
    [cards]
  );
  const mm = secondsLeft === null ? "" : `${Math.floor(secondsLeft / 60)}:${String(secondsLeft % 60).padStart(2, "0")}`;

  return (
    <main id="main" tabIndex={-1} className="focus-mode">
      <h1 className="page-title" tabIndex={-1}>Focus mode</h1>
      <p><small>One idea at a time. No animations. Leave whenever you want.</small></p>

      {!id && (
        <section aria-labelledby="pick-heading">
          <h2 id="pick-heading">Pick material</h2>
          {docs === null ? (
            <p>Loading…</p>
          ) : docs.length === 0 ? (
            <p><Link to="/library">Upload something first →</Link></p>
          ) : (
            <p>
              <label htmlFor="focus-doc">Document</label>
              <br />
              <select
                id="focus-doc"
                value={selectedDoc}
                onChange={(e) => setSelectedDoc(e.target.value)}
              >
                <option value="">— choose —</option>
                {docs.map((d) => (
                  <option key={d.id} value={d.id}>{d.filename}</option>
                ))}
              </select>
            </p>
          )}
        </section>
      )}

      {!cards && (
        <section aria-labelledby="dur-heading">
          <h2 id="dur-heading">Session length</h2>
          <ul className="mood-row">
            {DURATIONS.map((m) => (
              <li key={m}>
                <button type="button" onClick={() => setMinutes(m)}>{m} min</button>
              </li>
            ))}
            <li>
              <label htmlFor="custom-min">Custom</label>{" "}
              <input
                id="custom-min"
                type="number"
                min={5}
                max={180}
                value={custom}
                onChange={(e) => setCustom(e.target.value)}
                style={{ width: "5rem" }}
              />{" "}
              min
            </li>
          </ul>
          <button
            type="button"
            disabled={!(id || selectedDoc)}
            onClick={() => setSecondsLeft((parseInt(custom, 10) || minutes) * 60)}
          >
            Start focus session
          </button>{" "}
          <button type="button" onClick={() => void begin()}>
            Just show my material
          </button>
        </section>
      )}

      {secondsLeft !== null && (
        <p role="timer" aria-live="off" className="score-pill">{mm}</p>
      )}

      {cards && (
        <section aria-live="polite">
          <h2>Idea {cardIndex + 1} of {total}</h2>
          <div className="beads" aria-hidden="true">
            {cards.map((_, i) => (
              <span key={i} className={i < cardIndex ? "done" : i === cardIndex ? "now" : ""} />
            ))}
          </div>
          <article className="task-card prose">
            <p>{cards[cardIndex]}</p>
          </article>
          <p>
            {cardIndex > 0 && (
              <button type="button" onClick={() => setCardIndex(cardIndex - 1)}>← Back</button>
            )}{" "}
            {cardIndex < total - 1 ? (
              <button type="submit" onClick={() => setCardIndex(cardIndex + 1)}>
                Next idea →
              </button>
            ) : (
              <button type="button" onClick={() => setCardIndex(total)}>
                Finish — take a break ☕
              </button>
            )}
          </p>
          {cardIndex >= total && (
            <p className="prose" role="status">
              Nice work. Step away from the screen for a few minutes — the plan will be here when you are back.
            </p>
          )}
          {(cardIndex + 1) % 3 === 0 && cardIndex < total - 1 && (
            <p><small>Break suggestion: two minutes of looking away from the screen now?</small></p>
          )}
        </section>
      )}
    </main>
  );
}
