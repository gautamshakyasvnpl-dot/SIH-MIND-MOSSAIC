import type { SensoryPrefs } from "../context/SensorySettings";

const DISPLAY_FIELDS = [
  "font_style",
  "line_spacing",
  "reduce_motion",
  "modality_affinity",
  "audio_autoplay",
  "chunk_size",
  "pace",
  "noise_sensitive",
] as const;

export function profileToSensoryPatch(
  profile: unknown,
  current: SensoryPrefs
): Partial<SensoryPrefs> | null {
  if (typeof profile !== "object" || profile === null) return null;
  const source = profile as Record<string, unknown>;
  const patch: Partial<SensoryPrefs> = {};
  for (const field of DISPLAY_FIELDS) {
    const value = source[field];
    if (value === undefined || value === current[field]) continue;
    Object.assign(patch, { [field]: value });
  }
  return Object.keys(patch).length > 0 ? patch : null;
}
