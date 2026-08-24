import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type SensoryPrefs = {
  modality_affinity: "text" | "audio" | "visual";
  chunk_size: "small" | "medium" | "large";
  font_style: "default" | "dyslexia_friendly";
  text_size: "normal" | "large";
  high_contrast: boolean;
  line_spacing: "normal" | "wide";
  reduce_motion: boolean;
  audio_autoplay: boolean;
  pace: "gentle" | "standard";
  noise_sensitive: boolean;
};

export const DEFAULT_PREFS: SensoryPrefs = {
  modality_affinity: "text",
  chunk_size: "medium",
  font_style: "default",
  text_size: "normal",
  high_contrast: false,
  line_spacing: "normal",
  reduce_motion: false,
  audio_autoplay: false,
  pace: "standard",
  noise_sensitive: false,
};

const STORAGE_KEY = "sahaik_sensory";

type SensoryContextValue = {
  prefs: SensoryPrefs;
  update: (p: Partial<SensoryPrefs>) => void;
};

const SensoryContext = createContext<SensoryContextValue | null>(null);

function loadPrefs(): SensoryPrefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_PREFS };
    const parsed = JSON.parse(raw) as Partial<SensoryPrefs>;
    return { ...DEFAULT_PREFS, ...parsed };
  } catch {
    return { ...DEFAULT_PREFS };
  }
}

function applyAttributes(prefs: SensoryPrefs): void {
  const root = document.documentElement;
  root.dataset.font = prefs.font_style;
  root.dataset.spacing = prefs.line_spacing;
  root.dataset.motion = prefs.reduce_motion ? "reduced" : "normal";
  root.dataset.textsize = prefs.text_size;
  root.dataset.contrast = prefs.high_contrast ? "high" : "normal";
}

export function SensorySettingsProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [prefs, setPrefs] = useState<SensoryPrefs>(loadPrefs);

  useEffect(() => {
    applyAttributes(prefs);
  }, [prefs]);

  const update = useCallback((p: Partial<SensoryPrefs>) => {
    setPrefs((prev) => {
      const next = { ...prev, ...p };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        // storage may be unavailable (private mode); in-memory prefs still work
      }
      return next;
    });
  }, []);

  const value = useMemo(() => ({ prefs, update }), [prefs, update]);

  return (
    <SensoryContext.Provider value={value}>{children}</SensoryContext.Provider>
  );
}

export function useSensorySettings(): SensoryContextValue {
  const ctx = useContext(SensoryContext);
  if (!ctx) throw new Error("useSensorySettings outside provider");
  return ctx;
}
