import { useState } from "react";
import {
  askDocument,
  type AskResponse,
} from "../lib/api";

export default function AskPanel({ docId }: { docId: string }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function onAsk() {
    if (!question.trim()) return;
    setBusy(true);
    setStatus("Looking through the document…");
    try {
      const res = await askDocument(docId, question);
      setResult(res);
      setStatus("");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not answer");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="ask-heading">
      <h2 id="ask-heading">Ask this document</h2>
      <p>
        <label htmlFor="question">Your question</label>
        <br />
        <input
          id="question"
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void onAsk();
          }}
          style={{ width: "min(28rem, 100%)" }}
        />
      </p>
      <button type="button" onClick={onAsk} disabled={busy || !question.trim()}>
        {busy ? "Thinking…" : "Ask"}
      </button>
      <p role="status" aria-live="polite">
        {status}
      </p>
      {result && (
        <div>
          <article className="prose">
            <p>{result.answer}</p>
          </article>
          {result.sources.length > 0 && (
            <>
              <h3>From the document</h3>
              <ul className="source-list">
                {result.sources.map((s) => (
                  <li key={s.chunk_index}>
                    <small>{s.snippet}…</small>
                  </li>
                ))}
              </ul>
            </>
          )}
          {!result.used_llm && (
            <p>
              <small>Answered offline from matching text (no AI key set).</small>
            </p>
          )}
        </div>
      )}
    </section>
  );
}
