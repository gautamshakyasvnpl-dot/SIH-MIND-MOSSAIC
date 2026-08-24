const MOOD_SUGGESTIONS: Record<string, string> = {
  "1": "Try box breathing: in 4s, hold 4s, out 4s, hold 4s — four rounds. The Wellbeing page has the full guide and the Equal Opportunity Cell / counselling line.",
  "2": "A five-minute break away from the screen could reset your focus before your next card.",
  "3": "You are in the middle of the pack today — steady is fine. One card at a time.",
};

export function suggestForMood(suggestionText: string): string {
  const lower = suggestionText.toLowerCase();
  if (lower.includes("breathing") || lower.includes("counselling")) {
    return MOOD_SUGGESTIONS["1"];
  }
  if (lower.includes("break")) return MOOD_SUGGESTIONS["2"];
  return MOOD_SUGGESTIONS["3"];
}
