import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  getMemory,
  getPreferences,
  getQuiz,
  getReader,
  postExplain,
  postInteraction,
  type MemoryOut,
  type QuizItem,
  type ReaderCard,
  type ScoresOut,
} from "../lib/api";
import { usePageTitle } from "../hooks/usePageTitle";

const FEEDBACK_EVENTS: [string, string][] = [
  ["👍 Helpful", "thumbs_up"],
  ["👎 Not helpful", "thumbs_down"],
  ["Too long", "feedback_too_long"],
  ["Too difficult", "requested_simpler"],
  ["Need example", "feedback_need_example"],
];

function speak(text: string) {
  if (!("speechSynthesis" in window)) return false;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  window.speechSynthesis.speak(utter);
  return true;
}

export default function Reader() {
  const { id } = useParams();
  const [reader, setReader] = useState<Awaited<ReturnType<typeof getReader>> | null>(null);
  const [prefs, setPrefs] = useState<ScoresOut | null>(null);
  const [memory, setMemory] = useState<MemoryOut | null>(null);
  const [levels, setLevels] = useState<Record<number, number>>({});
  const [texts, setTexts] = useState<Record<number, string>>({});
  const [cardMsg, setCardMsg] = useState("");
  const [quiz, setQuiz] = useState<QuizItem[] | null>(null);
  const [picked, setPicked] = useState<Record<string, number>>({});
  const [status, setStatus] = useState("Loading reader…");
  const [showWhy, setShowWhy] = useState(false);

  usePageTitle(reader?.filename ?? "Adaptive reader");

  useEffect(() => {
    if (!id) return;
    void getReader(id)
      .then((r) => {
        setReader(r);
        setLevels(
          Object.fromEntries(r.cards.map((c) => [c.index, r.presentation.start_level]))
        );
        setStatus("");
        void getPreferences().then(setPrefs).catch(() => {});
        void getMemory().then(setMemory).catch(() => {});
      })
      .catch((err) =>
        setStatus(err instanceof Error ? err.message : "Could not load the reader")
      );
  }, [id]);

  const signal = useCallback(
    async (event: string, concept?: string, metadata?: Record<string, unknown>) => {
      try {
        const res = await postInteraction(event, {
          document_id: id ?? undefined,
          concept,
          metadata,
        });
        setPrefs(res);
      } catch {
        // preference update is best-effort; never block learning flow
      }
    },
    [id]
  );

  async function changeLevel(card: ReaderCard, delta: number) {
    const current = levels[card.index] ?? 4;
    const next = Math.max(1, Math.min(5, current + delta));
    if (next === current) return;
    const res = await postExplain(card.technical, next);
    setLevels((p) => ({ ...p, [card.index]: next }));
    setTexts((p) => ({ ...p, [card.index]: res.text }));
    setCardMsg(`Level ${next} of 5 (heuristic ladder).`);
    void signal(next < current ? "requested_simpler" : "explain_deeper_stepwise", card.concept ?? undefined);
  }

  async function runTransform(card: ReaderCard, transform: "analogy" | "bullets" | "summary" | "translate") {
    try {
      const res = await postExplain(card.technical, levels[card.index] ?? 4, undefined, transform);
      setTexts((p) => ({ ...p, [card.index]: res.text }));
      setCardMsg(`${transform[0].toUpperCase()}${transform.slice(1)} ready (${res.engine}).`);
      if (transform === "analogy") void signal("explain_deeper_stepwise", card.concept ?? undefined);
    } catch (err) {
      setCardMsg(err instanceof Error ? err.message : "That transform is unavailable right now.");
    }
  }

  async function loadQuiz() {
    if (!id) return;
    try {
      const res = await getQuiz(id, 3);
      setQuiz(res.items);
      void signal("quiz_started");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not build a quiz for this document");
    }
  }

  function answerQuestion(item: QuizItem, optionIdx: number) {
    if (item.id in picked) return;
    setPicked((p) => ({ ...p, [item.id]: optionIdx }));
    const correct = optionIdx === item.answer_index;
    void signal(correct ? "quiz_correct" : "quiz_incorrect", item.concept ?? undefined, {
      format: "quiz",
    });
    void getMemory().then(setMemory).catch(() => {});
  }

  if (status && !reader) {
    return (
      <main id="main" tabIndex={-1}>
        <h1 className="page-title" tabIndex={-1}>Adaptive reader</h1>
        <p role="status" aria-live="polite">{status}</p>
      </main>
    );
  }

  const pres = reader!.presentation;

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>{reader!.filename} — adaptive reader</h1>
      <section aria-labelledby="why-heading">
        <button type="button" aria-expanded={showWhy} onClick={() => setShowWhy(!showWhy)}>
          Why am I seeing this? {showWhy ? "▲" : "▼"}
        </button>
        {showWhy && (
          <div className="prose">
            <ul>
              {(prefs?.profile_lines?.length
                ? prefs.profile_lines
                : pres.hints_explanation
              ).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
            <p>
              <small>
                These are learning-preference scores you can view or edit any time in the{" "}
                <Link to="/preferences">personalization center</Link> — never diagnoses.
              </small>
            </p>
          </div>
        )}
      </section>

      {pres.prefer_audio && (
        <p role="note" className="recommend-chip">
          <strong>Tip:</strong> <small>You often use audio — every card has a read-aloud button.</small>
        </p>
      )}

      {reader!.cards.map((card) => {
        const level = levels[card.index] ?? pres.start_level;
        const body = texts[card.index] ?? (level >= 4 ? card.technical : card.simple);
        const struggled = memory?.struggled_concepts.find(
          (m) =>
            card.concept?.toLowerCase().includes(m.concept.toLowerCase()) ||
            m.concept.toLowerCase().includes(card.title.toLowerCase())
        );
        const exampleFirst = (!!struggled || pres.show_example_first) && !!card.example;
        return (
          <article className="task-card" key={card.index} aria-label={`Concept: ${card.title}`}>
            <h2>{card.title}</h2>
            {struggled && (
              <p className="emotion-note">
                You found “{struggled.concept}” tricky before ({struggled.misses}{" "}
                miss{struggled.misses > 1 ? "es" : ""}) — so this card starts with its
                example.
              </p>
            )}
            {exampleFirst && card.example && (
              <p className="emotion-note">Example first: {card.example}</p>
            )}
            <p className="prose">{body}</p>
            {!exampleFirst && card.example && (
              <p><small><strong>Example:</strong> {card.example}</small></p>
            )}
            <p>
              <button type="button" onClick={() => void changeLevel(card, -1)}>Make simpler</button>{" "}
              <button type="button" onClick={() => void changeLevel(card, 1)}>Explain deeper</button>{" "}
              <button type="button" onClick={() => void runTransform(card, "analogy")}>Show analogy</button>{" "}
              <button type="button" onClick={() => void runTransform(card, "bullets")}>As bullets</button>{" "}
              <button type="button" onClick={() => void runTransform(card, "summary")}>Summarize</button>{" "}
              <button
                type="button"
                title="Translation needs an AI key configured on the server"
                onClick={() => void runTransform(card, "translate")}
              >
                Translate
              </button>{" "}
              <button
                type="button"
                onClick={() => {
                  const ok = speak(card.example ?? card.technical);
                  if (ok) void signal("read_aloud", card.concept ?? undefined);
                  else setCardMsg("Read-aloud is not supported in this browser.");
                }}
              >
                Read aloud
              </button>
            </p>
            <p>
              <small>Explanation level {level} / 5 · heuristic ladder</small>
            </p>
            <fieldset>
              <legend>Quick feedback</legend>
              {FEEDBACK_EVENTS.map(([label, ev]) => (
                <button
                  key={ev}
                  type="button"
                  onClick={() => {
                    void signal(ev === "thumbs_up" || ev === "thumbs_down" ? ev : ev, card.concept ?? undefined, {
                      format: ev === "feedback_need_example" ? "example" : "simplified_text",
                    });
                    setCardMsg(`Thanks — noted (“${label}”). Your profile updated.`);
                  }}
                >
                  {label}
                </button>
              ))}
            </fieldset>
          </article>
        );
      })}

      {cardMsg && (
        <p role="status" aria-live="polite">{cardMsg}</p>
      )}

      <section aria-labelledby="quiz-heading">
        <h2 id="quiz-heading">Practice check</h2>
        {!quiz ? (
          <button type="button" onClick={() => void loadQuiz()}>Quiz me</button>
        ) : (
          quiz.map((q) => (
            <article className="task-card" key={q.id}>
              <h3>{q.question}</h3>
              {q.options.map((opt, i) => {
                const chosen = picked[q.id];
                const isAnswer = i === q.answer_index;
                const state =
                  chosen === undefined
                    ? ""
                    : isAnswer
                      ? " ✔ correct"
                      : i === chosen
                        ? " ✘ your pick"
                        : "";
                return (
                  <p key={opt}>
                    <label>
                      <input
                        type="radio"
                        name={q.id}
                        disabled={chosen !== undefined}
                        checked={chosen === i}
                        onChange={() => answerQuestion(q, i)}
                      />{" "}
                      <span>{opt}{state}</span>
                    </label>
                  </p>
                );
              })}
              <p><small>Concept area: {q.concept}</small></p>
            </article>
          ))
        )}
      </section>

      <p>
        <Link to={`/document/${id}`}>Full document tools (concept map, tutor, viva) →</Link>
      </p>
    </main>
  );
}
