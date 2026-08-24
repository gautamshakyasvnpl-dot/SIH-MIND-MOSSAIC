import { useCallback, useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { getConsents } from "../lib/api";
import { useDictation } from "../hooks/useDictation";

const VOICE_COMMANDS: Record<string, string> = {
  "open library": "/library",
  "open tasks": "/tasks",
  "open wellbeing": "/wellbeing",
};

export default function SiteHeader() {
  const navigate = useNavigate();
  const [voiceMsg, setVoiceMsg] = useState("");
  const [voiceConsent, setVoiceConsent] = useState<boolean | null>(null);

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

  const commands = {
    phrases: {
      "open library": () => navigate("/library"),
      "open tasks": () => navigate("/tasks"),
      "open wellbeing": () => navigate("/wellbeing"),
    },
    onCommand: (phrase: string) =>
      setVoiceMsg(`Voice command done: ${phrase}.`),
  };
  const dictation = useDictation(() => {}, commands);
  const voiceOff = voiceConsent === false;

  const toggleVoice = useCallback(() => {
    if (dictation.listening) {
      dictation.stop();
      setVoiceMsg("");
    } else {
      dictation.start();
      setVoiceMsg(
        `Listening for: ${Object.keys(VOICE_COMMANDS).join(", ")}.`
      );
    }
  }, [dictation]);

  function onLogout() {
    localStorage.removeItem("sahaik_token");
    navigate("/login");
  }

  return (
    <header className="site-header">
      <Link to="/dashboard" className="wordmark">
        <span className="mark" aria-hidden="true">
          स
        </span>
        <span>
          NEURO<span className="tilde">LEARN</span>
        </span>
      </Link>
      <nav className="site-nav" aria-label="Primary">
        <NavLink to="/dashboard">Home</NavLink>
        <NavLink to="/library">Library</NavLink>
        <NavLink to="/tasks">Sprints</NavLink>
        <NavLink to="/wellbeing">Wellbeing</NavLink>
        <NavLink to="/communicate">Communicate</NavLink>
        <NavLink to="/preferences">Preferences</NavLink>
        {voiceOff ? (
          <span className="voice-off-note">
            <Link to="/preferences" title="Voice input is off in your consent settings">
              Voice off
            </Link>
          </span>
        ) : (
          <button
            type="button"
            aria-pressed={dictation.listening}
            onClick={toggleVoice}
            title="Voice navigation — say: open library, open tasks, open wellbeing"
          >
            {dictation.listening ? "Listening…" : "🎙 Voice"}
          </button>
        )}
        <button type="button" onClick={onLogout}>
          Log out
        </button>
      </nav>
      <p role="status" aria-live="polite" style={{ display: voiceMsg ? undefined : "none", position: "absolute", left: "-9999px" }}>
        {voiceMsg}
      </p>
      {dictation.error && (
        <p role="alert" aria-live="polite">
          {dictation.error}{" "}
          <Link to="/preferences">Open Preferences</Link>.
        </p>
      )}
    </header>
  );
}
