import { useCallback, useEffect, useRef } from "react";
import { getProfile } from "../lib/api";
import { profileToSensoryPatch } from "../lib/profileSync";
import { useSensorySettings } from "../context/SensorySettings";

export function useProfileSync(): () => Promise<void> {
  const { prefs, update } = useSensorySettings();
  const latest = useRef({ prefs, update });

  useEffect(() => {
    latest.current = { prefs, update };
  });

  return useCallback(async () => {
    try {
      const profile = await getProfile();
      const patch = profileToSensoryPatch(profile, latest.current.prefs);
      if (patch) latest.current.update(patch);
    } catch {
      // server unreachable or anonymous session: local sensory prefs stay as-is
    }
  }, []);
}
