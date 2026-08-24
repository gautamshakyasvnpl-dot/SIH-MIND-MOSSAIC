import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { putProfile, type Profile } from "../lib/api";
import { useSensorySettings } from "../context/SensorySettings";
import { profileToSensoryPatch } from "../lib/profileSync";
import ConsentSection from "../components/ConsentSection";
import { usePageTitle } from "../hooks/usePageTitle";

type Answers = Partial<Profile>;

const STEPS = 8;

const REQUIRED_BY_STEP: Partial<Record<number, keyof Answers>> = {
  0: "modality_affinity",
  1: "chunk_size",
  2: "font_style",
  3: "line_spacing",
  5: "pace",
};

const ALL_REQUIRED: (keyof Answers)[] = [
  "modality_affinity",
  "chunk_size",
  "font_style",
  "line_spacing",
  "pace",
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { prefs: sensory, update: updateSensory } = useSensorySettings();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  usePageTitle("Learning profile setup");

  function set<K extends keyof Answers>(key: K, value: Answers[K]) {
    setAnswers((prev) => ({ ...prev, [key]: value }));
  }

  async function finish(final: Answers) {
    setBusy(true);
    setError(null);
    try {
      const saved = await putProfile({
        ...answers,
        ...final,
        onboarding_complete: true,
      });
      const patch = profileToSensoryPatch(saved, sensory);
      if (patch) updateSensory(patch);
      navigate("/library");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save profile");
      setBusy(false);
    }
  }

  const requiredKey = REQUIRED_BY_STEP[step];
  const stepValid =
    requiredKey === undefined || answers[requiredKey] !== undefined;
  const allValid = ALL_REQUIRED.every((k) => answers[k] !== undefined);

  function next(e: FormEvent) {
    e.preventDefault();
    if (step < STEPS - 1) setStep(step + 1);
  }

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>Set up your learning profile</h1>
      <p>
        Step {step + 1} of {STEPS}. You can change these later in settings.
      </p>
      <div
        className="beads"
        role="progressbar"
        aria-valuenow={step + 1}
        aria-valuemin={1}
        aria-valuemax={STEPS}
        aria-label="Onboarding progress"
      >
        {Array.from({ length: STEPS }, (_, i) => (
          <span key={i} className={i < step ? "done" : i === step ? "now" : ""} />
        ))}
      </div>
      <form onSubmit={next}>
        {step === 0 && (
          <fieldset className="card choice-list">
            <legend>How do you prefer to take in new information?</legend>
            {(
              [
                ["text", "Reading text"],
                ["audio", "Listening"],
                ["visual", "Pictures and diagrams"],
              ] as const
            ).map(([value, label]) => (
              <p key={value}>
                <label>
                  <input
                    type="radio"
                    name="modality"
                    checked={answers.modality_affinity === value}
                    onChange={() => set("modality_affinity", value)}
                  />{" "}
                  {label}
                </label>
              </p>
            ))}
          </fieldset>
        )}
        {step === 1 && (
          <fieldset className="card choice-list">
            <legend>How much text feels comfortable at one time?</legend>
            {(
              [
                ["small", "A little at a time (a few sentences)"],
                ["medium", "A short paragraph"],
                ["large", "Longer sections are fine"],
              ] as const
            ).map(([value, label]) => (
              <p key={value}>
                <label>
                  <input
                    type="radio"
                    name="chunk"
                    checked={answers.chunk_size === value}
                    onChange={() => set("chunk_size", value)}
                  />{" "}
                  {label}
                </label>
              </p>
            ))}
          </fieldset>
        )}
        {step === 2 && (
          <fieldset className="card choice-list">
            <legend>Which letter style is easier to read?</legend>
            {(
              [
                ["default", "Standard letters"],
                ["dyslexia_friendly", "Dyslexia-friendly letters (wider spacing)"],
              ] as const
            ).map(([value, label]) => (
              <p key={value}>
                <label>
                  <input
                    type="radio"
                    name="font"
                    checked={answers.font_style === value}
                    onChange={() => set("font_style", value)}
                  />{" "}
                  {label}
                </label>
              </p>
            ))}
          </fieldset>
        )}
        {step === 3 && (
          <fieldset className="card choice-list">
            <legend>How much space between lines of text?</legend>
            {(
              [
                ["normal", "Normal spacing"],
                ["wide", "Extra space between lines"],
              ] as const
            ).map(([value, label]) => (
              <p key={value}>
                <label>
                  <input
                    type="radio"
                    name="spacing"
                    checked={answers.line_spacing === value}
                    onChange={() => set("line_spacing", value)}
                  />{" "}
                  {label}
                </label>
              </p>
            ))}
          </fieldset>
        )}
        {step === 4 && (
          <fieldset className="card choice-list">
            <legend>Comfort options</legend>
            <p>
              <label>
                <input
                  type="checkbox"
                  checked={answers.reduce_motion ?? false}
                  onChange={(e) => set("reduce_motion", e.target.checked)}
                />{" "}
                Reduce movement and animation on screen
              </label>
            </p>
            <p>
              <label>
                <input
                  type="checkbox"
                  checked={answers.audio_autoplay ?? false}
                  onChange={(e) => set("audio_autoplay", e.target.checked)}
                />{" "}
                Start playing audio automatically when available
              </label>
            </p>
            <p>
              <label>
                <input
                  type="checkbox"
                  checked={answers.noise_sensitive ?? false}
                  onChange={(e) => set("noise_sensitive", e.target.checked)}
                />{" "}
                I am sensitive to noise
              </label>
            </p>
            <p>
              <label>
                <input
                  type="checkbox"
                  checked={sensory.text_size === "large"}
                  onChange={(e) =>
                    updateSensory({ text_size: e.target.checked ? "large" : "normal" })
                  }
                />{" "}
                Larger text (applies immediately)
              </label>
            </p>
            <p>
              <label>
                <input
                  type="checkbox"
                  checked={sensory.high_contrast}
                  onChange={(e) => updateSensory({ high_contrast: e.target.checked })}
                />{" "}
                High contrast mode (applies immediately)
              </label>
            </p>
          </fieldset>
        )}
        {step === 5 && (
          <fieldset className="card choice-list">
            <legend>What learning pace suits you best?</legend>
            {(
              [
                ["gentle", "Gentle: shorter steps, more explanation"],
                ["standard", "Standard: normal flow"],
              ] as const
            ).map(([value, label]) => (
              <p key={value}>
                <label>
                  <input
                    type="radio"
                    name="pace"
                    checked={answers.pace === value}
                    onChange={() => set("pace", value)}
                  />{" "}
                  {label}
                </label>
              </p>
            ))}
          </fieldset>
        )}
        {step === 6 && (
          <div className="card">
            <ConsentSection heading="Your consent choices" />
          </div>
        )}
        {step === 7 && (
          <fieldset className="card">
            <legend>Ready to save your profile?</legend>
            <ul className="review-table">
              {Object.entries({
                Modality: answers.modality_affinity,
                "Chunk size": answers.chunk_size,
                Font: answers.font_style,
                Spacing: answers.line_spacing,
                "Reduce motion": answers.reduce_motion ? "yes" : "no",
                "Audio autoplay": answers.audio_autoplay ? "yes" : "no",
                Pace: answers.pace,
                "Noise sensitive": answers.noise_sensitive ? "yes" : "no",
              }).map(([k, v]) => (
                <li key={k}>
                  {k}: <strong>{String(v)}</strong>
                </li>
              ))}
            </ul>
            {!allValid && (
              <p>
                <small>Some choices are missing — go back to complete them.</small>
              </p>
            )}
            <button
              type="button"
              onClick={() => finish({})}
              disabled={busy || !allValid}
            >
              {busy ? "Saving…" : "Save and continue"}
            </button>
          </fieldset>
        )}
        {error && <p role="alert" aria-live="polite">{error}</p>}
        {step > 0 && step < STEPS - 1 && (
          <>
            <button type="button" onClick={() => setStep(step - 1)}>
              Back
            </button>{" "}
            <button type="submit" disabled={!stepValid}>Next</button>
          </>
        )}
        {step === 0 && (
          <button type="submit" disabled={!stepValid}>Next</button>
        )}
        {requiredKey !== undefined && !stepValid && (
          <p aria-live="polite">
            <small>Choose an option above to continue.</small>
          </p>
        )}
      </form>
    </main>
  );
}
