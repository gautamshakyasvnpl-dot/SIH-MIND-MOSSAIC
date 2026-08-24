import { useEffect, useState } from "react";
import { getConsents, putConsents, type Consents } from "../lib/api";

const CONSENT_ITEMS: [keyof Consents, string, string][] = [
  [
    "voice",
    "Voice processing",
    "When on: audio you record for dictation or server transcription is sent to the AI provider to turn it into text. When off: no audio leaves your device and voice input buttons are unavailable. Nothing audio-related is stored.",
  ],
  [
    "telemetry",
    "Telemetry (adaptive-learning signals)",
    "When on: actions like requesting simpler text or quiz answers are stored on the server with your account so the reader can adapt to you. When off: no learning signals are recorded.",
  ],
  [
    "memory",
    "Learning memory",
    "When on: concepts you found tricky are kept on the server with your account so review suggestions can be built. When off: nothing about struggled concepts is kept.",
  ],
];

export default function ConsentSection({ heading = "Your consent choices" }: { heading?: string }) {
  const [values, setValues] = useState<Consents>({ voice: false, telemetry: false, memory: false });
  const [loaded, setLoaded] = useState(false);
  const [status, setStatus] = useState("");
  const headingId = "consent-heading";

  useEffect(() => {
    let cancelled = false;
    getConsents()
      .then((c) => {
        if (cancelled) return;
        setValues(c);
        setLoaded(true);
      })
      .catch(() => {
        if (!cancelled) setStatus("Could not load your consent settings right now.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function save(next: Consents) {
    setValues(next);
    setStatus("Saving…");
    try {
      const saved = await putConsents(next);
      setValues(saved);
      setStatus("Consent saved.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not save consent right now.");
    }
  }

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId}>{heading}</h2>
      <fieldset>
        <legend>Optional features, all off by default</legend>
        {CONSENT_ITEMS.map(([key, label, description]) => (
          <div key={key}>
            <p>
              <label>
                <input
                  type="checkbox"
                  checked={values[key]}
                  disabled={!loaded}
                  onChange={(e) => void save({ ...values, [key]: e.target.checked })}
                />{" "}
                {label}
              </label>
            </p>
            <p>
              <small>{description}</small>
            </p>
          </div>
        ))}
      </fieldset>
      <p>
        <small>
          Typing and self-report check-ins always work, no matter how these are
          set. Anything stored can be exported or deleted from Preferences →
          Data controls.
        </small>
      </p>
      <p role="status" aria-live="polite">
        {status}
      </p>
    </section>
  );
}
