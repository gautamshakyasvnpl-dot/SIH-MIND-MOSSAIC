# NEUROLEARN — Demo Video Script (3:00)

Target runtime: 3 minutes. Format: screen recording with voiceover; captions burned in for accessibility. The script demonstrates the shipped product only — every scene below matches the real UI as of the feature freeze plus repair phase.

**[RECORD AFTER FINAL GATES]** Do not record until the pending human accessibility passes (keyboard-only golden path, NVDA walkthrough) are complete, so any last UI fixes make it on camera.

| # | Timecode | Screen | Narration |
|---|---|---|---|
| 1 | 00:00–00:15 | Full-screen slide of a dense lecture deck — wall of small text. Static frame with highlight boxes (respect reduced motion). | "This is a typical lecture slide. For neurodivergent learners — students with dyslexia, ADHD, or autism — walls of dense text aren't just unpleasant. They're a barrier to the actual content." |
| 2 | 00:15–00:30 | Landing → Register form (email, display name, password). Submit lands on Dashboard. | "NEUROLEARN is an AI-powered inclusive learning platform built for neurodivergent higher-education students. Registration takes seconds." |
| 3 | 00:30–01:00 | Onboarding wizard: modality, chunk size, font style, spacing, pace — selecting dyslexia-friendly font and wide spacing visibly re-renders the page. Then the **consent panel**: three toggles, voice / telemetry / memory, all shown **off by default**. Leave them off; continue. | "A short profiler asks how you learn best. This is a preference profile, explicitly not a diagnosis. Then you decide about voice input, interaction logging, and learning memory — every toggle starts off, and the app works fully without them." |
| 4 | 01:00–01:20 | Library → file picker → upload a `.pptx` → document card appears with type and size. | "Upload any lecture material — PowerPoint, PDF, Word, or plain text, up to twenty megabytes." |
| 5 | 01:20–01:50 | DocumentView: request simplified text + TTS. Simplified rendering appears with its **explanation** line; the **recommendation chip** cites profile fields ("You told us…"). Press play on the standard audio player. | "One click adapts the document to your profile, chunked and simplified — and every adaptation says *why*. The recommender suggests a format based on your own stated preferences. Read it, hear it, or both." |
| 6 | 01:50–02:10 | **Ask** panel: type a question about the document → grounded answer with cited source snippets. Then open **Viva Studio**: start practice viva; answer one question aloud or typed; feedback and score appear. Note on screen: *exactly five questions per session*. | "Ask the document anything — answers come only from your material, with sources. Practice a viva: five questions, honest feedback and a score on each answer." |
| 7 | 02:10–02:30 | Sprint board: create a task → sprint plan appears sized to your pace → tick one sprint done. Wellbeing page: log mood 2 of 5 → suggestion shows box-breathing steps ("in four seconds, hold four, out four, hold four") plus counselling escalation line. | "Big assignments become small sprints that match your pace. And wellbeing check-ins respond to low moods with concrete grounding exercises and where to find people, not platitudes." |
| 8 | 02:30–02:50 | Preferences: "Why am I seeing this?" explanations, consent toggles again, **Export my data** downloads a JSON file, then **Delete my account** confirmation dialog (do not confirm on camera). | "Your data is yours: see why the system adapted, change consents anytime, export everything as a file, or delete your whole account in one confirmed action." |
| 9 | 02:50–03:00 | End card: NEUROLEARN wordmark, problem statement ID GGSIPU2605, team — USAR, GGSIPU. | "NEUROLEARN — learning that adapts to the learner. Smart India Hackathon 2026, GGSIPU2605." |

## Production notes

- **Captions:** burn in English subtitles; keep narration sentences short.
- **Reduced motion:** no animated flourishes promised anywhere in this script; if any transition is used, honour the same reduced-motion rules as the product itself.
- **Screen recording setup:** 1920×1080, browser zoom ≥ 125%, cursor enlarged, visible focus ring when keyboard navigation is shown.
- **Honesty rule:** show only implemented behavior. No camera features appear anywhere in the product — do not frame a webcam in any shot. If a take requires unimplemented UI, re-script rather than mock results.
- **Consent accuracy:** the consent panel must be recorded with all three toggles visibly OFF at first appearance; if voice dictation is demonstrated later in the viva scene, either enable voice consent on camera first or use typed input instead.
- **Spec alignment:** the full-product spec (§6) plans a Viva Studio opening for the final submission video; this script opens on the dense-slide pain point and shows Viva Studio inside the product tour instead.
