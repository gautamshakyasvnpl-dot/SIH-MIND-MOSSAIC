import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  answerViva,
  fetchProtectedMediaBlobUrl,
  getConsents,
  getVivaTranscript,
  startViva,
  type VivaAnswerOut,
  type VivaTranscript,
} from "../lib/api";
import { useDictation } from "../hooks/useDictation";
import { usePageTitle } from "../hooks/usePageTitle";

type VivaTurnView = VivaTranscript["turns"][number];

function vivaStorageKey(docId: string): string {
  return `neurolearn_viva_${docId}`;
}

export default function VivaStudio() {
  const { id } = useParams();
  usePageTitle("Viva practice");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [turnCount, setTurnCount] = useState(0);
  const [done, setDone] = useState(false);
  const [transcript, setTranscript] = useState<VivaTurnView[]>([]);
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [voiceConsent, setVoiceConsent] = useState<boolean | null>(null);
  const [audioSrc, setAudioSrc] = useState<string | null>(null);
  const [audioState, setAudioState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const dictation = useDictation((text) =>
    setAnswer((prev) => (prev ? `${prev} ${text}` : text))
  );

  useEffect(
    () => () => {
      if (audioSrc) URL.revokeObjectURL(audioSrc);
    },
    [audioSrc]
  );

  useEffect(() => {
    if (!sessionId || !question) {
      setAudioState("idle");
      setAudioSrc(null);
      return;
    }
    let cancelled = false;
    setAudioState("loading");
    fetchProtectedMediaBlobUrl("question_audio", sessionId)
      .then((url) => {
        if (cancelled) {
          URL.revokeObjectURL(url);
          return;
        }
        setAudioSrc((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
        });
        setAudioState("ready");
      })
      .catch(() => {
        if (!cancelled) setAudioState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId, question]);

  useEffect(() => {
    let cancelled = false;
    getConsents()
      .then((c) => {
        if (!cancelled) setVoiceConsent(c.voice);
      })
      .catch(() => {
        if (!cancelled) setVoiceConsent(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!id) return;
    const saved = sessionStorage.getItem(vivaStorageKey(id));
    if (!saved) return;
    let cancelled = false;
    getVivaTranscript(saved)
      .then((t) => {
        if (cancelled) return;
        setSessionId(t.session_id);
        setTranscript(
          t.turns.map((turn) => ({ ...turn, index: turn.index + 1 }))
        );
        const pending = [...t.turns].reverse().find((turn) => turn.answer === null);
        if (!t.done && pending) {
          setQuestion(pending.question);
          setTurnCount(pending.index + 1);
          setStatus(
            `Welcome back — question ${pending.index + 1} of 5 is waiting whenever you are ready.`
          );
        } else {
          setDone(true);
          setQuestion("");
          setStatus("Your practice viva is complete — the full transcript is below.");
        }
      })
      .catch(() => {
        if (!cancelled) sessionStorage.removeItem(vivaStorageKey(id));
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  async function onStart() {
    if (!id) return;
    setBusy(true);
    setStatus("Preparing your practice viva…");
    try {
      const res = await startViva(id);
      sessionStorage.setItem(vivaStorageKey(id), res.session_id);
      setSessionId(res.session_id);
      setTranscript([
        { index: 1, question: res.question, answer: null, feedback: null, score: null },
      ]);
      setQuestion(res.question);
      setTurnCount(1);
      setDone(false);
      setStatus("Answer in your own words, then submit. Take your time.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not start viva right now. Please try again in a moment.");
    } finally {
      setBusy(false);
    }
  }

  async function onSubmit() {
    if (!sessionId || !answer.trim()) return;
    const submitted = answer.trim();
    setBusy(true);
    try {
      const res: VivaAnswerOut = await answerViva(sessionId, submitted);
      setTranscript((prev) => {
        const next = prev.map((t, i) =>
          i === prev.length - 1 && t.answer === null
            ? { ...t, answer: submitted, feedback: res.feedback, score: res.score }
            : t
        );
        if (!res.done && res.next_question) {
          next.push({
            index: res.turn_count,
            question: res.next_question,
            answer: null,
            feedback: null,
            score: null,
          });
        }
        return next;
      });
      if (res.done) {
        setDone(true);
        setQuestion("");
        setStatus("Viva complete. Well done — review the feedback below.");
      } else {
        setQuestion(res.next_question ?? "");
        setTurnCount(res.turn_count);
        setStatus(`Question ${res.turn_count} of 5.`);
      }
      setAnswer("");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not submit answer");
    } finally {
      setBusy(false);
    }
  }

  const voiceOff = voiceConsent === false;

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>Viva practice studio</h1>
      <p>
        Five questions about this document. Answer by typing or with your
        voice — whichever is easier right now.
      </p>
      <p role="status" aria-live="polite">
        {status}
      </p>
      {!sessionId ? (
        !done && (
          <button type="button" onClick={() => void onStart()} disabled={busy}>
            {busy ? "Preparing…" : "Start practice viva"}
          </button>
        )
      ) : (
        <>
          {question && (
            <section aria-labelledby="q-heading">
              <h2 id="q-heading">
                Question {turnCount} of 5
              </h2>
              <article className="prose">
                <p>{question}</p>
              </article>
              {sessionId && (
                <p>
                  {audioState === "ready" && audioSrc ? (
                    <>
                      <audio controls preload="none" src={audioSrc} />{" "}
                      <small>Listen to the question</small>
                    </>
                  ) : audioState === "error" ? (
                    <small role="status">
                      Question audio is unavailable right now — the written question above works
                      too.
                    </small>
                  ) : (
                    <small role="status" aria-live="polite">
                      Preparing question audio…
                    </small>
                  )}
                </p>
              )}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void onSubmit();
                }}
              >
                <p>
                  <label htmlFor="answer">Your answer</label>
                  <br />
                  <textarea
                    id="answer"
                    rows={4}
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    style={{ width: "min(32rem, 100%)" }}
                  />
                </p>
                <button type="submit" disabled={busy || !answer.trim()}>
                  {busy ? "Checking…" : "Submit answer"}
                </button>{" "}
                {!voiceOff && (
                  <button
                    type="button"
                    aria-pressed={dictation.listening}
                    onClick={() => (dictation.listening ? dictation.stop() : dictation.start())}
                  >
                    {dictation.listening
                      ? "Stop listening"
                      : "Speak answer"}
                  </button>
                )}{" "}
                {voiceOff && (
                  <small>
                    Voice input is off in your consent settings —{" "}
                    <Link to="/preferences">change in Preferences</Link>. Typing always works.
                  </small>
                )}
              </form>
              {!dictation.supported && (
                <p>
                  <small>
                    Browser voice input unavailable — your recording goes to
                    server transcription, or you can type.
                  </small>
                </p>
              )}
              {(dictation.error || dictation.consentBlocked) && (
                <p role="alert" aria-live="polite">
                  {dictation.error}
                  {dictation.consentBlocked && (
                    <>
                      {" "}
                      <Link to="/preferences">Open Preferences</Link>.
                    </>
                  )}
                </p>
              )}
            </section>
          )}
          {transcript.length > 0 && (
            <section aria-labelledby="transcript-heading">
              <h2 id="transcript-heading">Session transcript</h2>
              {done && (
                <p>
                  <span className="score-pill">Viva complete — 5 of 5 answered</span>
                </p>
              )}
              <ol className="source-list">
                {transcript.map((t) => (
                  <li key={t.index}>
                    <h3>Question {t.index} of 5</h3>
                    <article className="prose">
                      <p>{t.question}</p>
                      {t.answer === null ? (
                        <p><small>Not answered yet.</small></p>
                      ) : (
                        <>
                          <p>
                            <strong>Your answer:</strong> {t.answer}
                          </p>
                          {t.feedback && <p>{t.feedback}</p>}
                          {t.score !== null && (
                            <p>
                              <span className="score-pill">Score: {t.score} / 2</span>
                            </p>
                          )}
                        </>
                      )}
                    </article>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </>
      )}
    </main>
  );
}
