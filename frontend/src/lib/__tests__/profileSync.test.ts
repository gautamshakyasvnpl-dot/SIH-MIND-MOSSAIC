import { describe, expect, it } from "vitest";
import { DEFAULT_PREFS } from "../../context/SensorySettings";
import { profileToSensoryPatch } from "../profileSync";

describe("profileToSensoryPatch", () => {
  it("returns null for missing profiles", () => {
    expect(profileToSensoryPatch(null, DEFAULT_PREFS)).toBeNull();
    expect(profileToSensoryPatch(undefined, DEFAULT_PREFS)).toBeNull();
    expect(profileToSensoryPatch("nope", DEFAULT_PREFS)).toBeNull();
  });

  it("maps only server display fields that differ", () => {
    const patch = profileToSensoryPatch(
      {
        font_style: "dyslexia_friendly",
        line_spacing: "normal",
        reduce_motion: true,
        onboarding_complete: true,
      },
      DEFAULT_PREFS
    );
    expect(patch).toEqual({
      font_style: "dyslexia_friendly",
      reduce_motion: true,
    });
  });

  it("returns null when everything already matches", () => {
    const patch = profileToSensoryPatch(DEFAULT_PREFS, DEFAULT_PREFS);
    expect(patch).toBeNull();
  });
});
