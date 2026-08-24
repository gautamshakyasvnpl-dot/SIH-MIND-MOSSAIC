import { useCallback, useEffect, useRef, useState } from "react";
import { transcribeAudio } from "../lib/api";

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start(): void;
  stop(): void;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};

function getRecognitionCtor():
  | (new () => SpeechRecognitionLike)
  | null {
  const w = window as unknown as Record<string, unknown>;
  return (w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null) as
    | (new () => SpeechRecognitionLike)
    | null;
}

export type DictationCommands = {
  phrases: Record<string, () => void>;
  onCommand?: (phrase: string) => void;
};

function matchCommand(
  text: string,
  commands?: DictationCommands
): { handled: boolean; phrase: string } {
  if (!commands) return { handled: false, phrase: "" };
  const normalized =
    ` ${text.toLowerCase().replace(/[^\w\s]/g, " ").replace(/\s+/g, " ").trim()} `;
  for (const phrase of Object.keys(commands.phrases)) {
    const needle = ` ${phrase.toLowerCase().replace(/\s+/g, " ")} `;
    if (normalized.includes(needle)) {
      commands.phrases[phrase]();
      commands.onCommand?.(phrase);
      return { handled: true, phrase };
    }
  }
  return { handled: false, phrase: "" };
}

export function useDictation(
  onText: (text: string) => void,
  commands?: DictationCommands
) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [consentBlocked, setConsentBlocked] = useState(false);
  const [recordingFallback, setRecordingFallback] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const onTextRef = useRef(onText);
  onTextRef.current = onText;
  const commandsRef = useRef<DictationCommands | undefined>(commands);
  commandsRef.current = commands;

  useEffect(() => {
    setSupported(getRecognitionCtor() !== null);
    return () => {
      recognitionRef.current?.stop();
      recorderRef.current?.state === "recording" && recorderRef.current.stop();
    };
  }, []);

  const stopBrowserRecognition = useCallback(() => {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setListening(false);
  }, []);

  const sendToServerStt = useCallback(async (blob: Blob) => {
    setError(null);
    try {
      const res = await transcribeAudio(blob);
      if (!res.text) {
        setError("Server transcription unavailable — please type instead.");
        return;
      }
      const hit = matchCommand(res.text, commandsRef.current);
      if (!hit.handled) onTextRef.current(res.text);
    } catch (err) {
      if ((err as { status?: number }).status === 403) {
        setConsentBlocked(true);
        setError("Voice input is off in your consent settings — please type instead.");
      } else {
        setError("Server transcription unavailable — please type instead.");
      }
    }
  }, []);

  const start = useCallback(() => {
    setError(null);
    setConsentBlocked(false);
    const Ctor = getRecognitionCtor();
    if (Ctor) {
      const rec = new Ctor();
      rec.lang = "en-US";
      rec.continuous = false;
      rec.interimResults = false;
      rec.onresult = (event) => {
        let text = "";
        for (let i = 0; i < event.results.length; i += 1) {
          text += event.results[i][0].transcript;
        }
        const trimmed = text.trim();
        if (!trimmed) return;
        const hit = matchCommand(trimmed, commandsRef.current);
        if (!hit.handled) onTextRef.current(trimmed);
      };
      rec.onerror = () => {
        setError("Voice input failed — please type instead.");
        setListening(false);
      };
      rec.onend = () => setListening(false);
      recognitionRef.current = rec;
      try {
        rec.start();
        setListening(true);
        return;
      } catch {
        // fall through to MediaRecorder path
      }
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Voice input not supported in this browser — please type.");
      return;
    }
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        const mime = MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "";
        const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
        chunksRef.current = [];
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };
        recorder.onstop = () => {
          stream.getTracks().forEach((t) => t.stop());
          setRecordingFallback(false);
          const blob = new Blob(chunksRef.current, { type: mime || "audio/webm" });
          if (blob.size > 0) void sendToServerStt(blob);
        };
        recorderRef.current = recorder;
        recorder.start();
        setRecordingFallback(true);
        setListening(true);
      })
      .catch(() => {
        setError("Microphone access denied — please type instead.");
      });
  }, [sendToServerStt]);

  const stop = useCallback(() => {
    if (recognitionRef.current) {
      stopBrowserRecognition();
      return;
    }
    if (
      recorderRef.current &&
      recorderRef.current.state === "recording"
    ) {
      recorderRef.current.stop();
      setListening(false);
    }
  }, [stopBrowserRecognition]);

  return {
    listening,
    supported,
    recordingFallback,
    error,
    consentBlocked,
    start,
    stop,
    clearError: () => setError(null),
  };
}
