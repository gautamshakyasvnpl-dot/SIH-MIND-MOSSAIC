# NEUROLEARN (repo codename SahAIk) — User Testing Report

> **Status: methodology locked; human sessions pending scheduling with the Equal Opportunity Cell.**
> Sections marked **[PENDING]** await live participants. Everything else is complete, including pre-session automated findings that will be re-verified during sessions.
>
> Companion instruments in this directory:
> - `informed-consent-form.md` — plain-language participant consent form
> - `sus-survey.md` — System Usability Scale questionnaire
>
> No session begins before signed consent is on file for every participant.

## 1. Study metadata

- **Product version tested:** repair-phase-complete build of the frozen Week 1–3 feature set plus the adaptive-reader personalization loop (auth, profiler onboarding with granular consents, documents/adaptation/TTS, tutor Q&A with sources, sprints, five-question vivas, wellbeing check-ins, recommender, privacy export/deletion)
- **Session dates:** **[PENDING]**
- **Location / mode:** on-campus room booked through EOC (soft lighting, quiet); remote screen-share option for participants who prefer home environments
- **Facilitator / note-taker:** UX/Accessibility lead + scribe
- **Ethics reference:** design spec §2.4 and §3.3 — self-report first; no camera-based emotion recognition anywhere in the product (the build contains no camera UI and no mounted face-emotion endpoint); opt-in voice/telemetry/memory toggles defaulting to off; no dark patterns; plain-language AI disclosure on every agent surface

## 2. Participants

Target per spec §9: **5–8 neurodivergent students**, recruited via the university Equal Opportunity Cell / counselling services.

| ID | Age band | Self-described profile | Prior assistive-tech use | Consent signed |
|---|---|---|---|---|
| P1–P8 | [PENDING] | | | |

**Recruitment notes:** [PENDING] — EOC coordinator introduction secured; scheduling in progress.

**Backup plan (if campus recruitment stalls):** recruitment via neurodivergent-led online communities, and/or clearly-labeled synthetic personas. Any persona-derived data will be disclosed prominently in §5–§6 and flagged again in §8.

## 3. Procedure

1. Welcome; plain-language study explanation; review and sign `informed-consent-form.md`.
2. Confirm accommodations needs (breaks, noise, lighting, session length cap).
3. Task block (~30–40 min), think-aloud optional — participant's choice. Facilitator notes the state of the in-app consent toggles whenever voice input or logged interactions are exercised, since all three toggles start off by design.
4. SUS questionnaire (`sus-survey.md`).
5. Short semi-structured debrief.
6. Thank-you; compensation per EOC arrangement; reminder of data handling rights (export from Preferences; full account deletion).

## 4. Tasks

Golden paths from spec §9. All listed tasks are implemented in the current build.

| # | Task | Path | Phase | Completed | Time | Notes |
|---|---|---|---|---|---|---|
| T1 | Register an account and log in | auth | W1 ✅ | [PENDING] | | |
| T2 | Complete profiler onboarding; set dyslexia-friendly font + wide spacing | profile + sensory settings | W1 ✅ | [PENDING] | | |
| T3 | Review the consent panel (voice / telemetry / memory, defaults off) and make deliberate choices | consents (onboarding + preferences) | W1 ✅ | [PENDING] | | |
| T4 | Upload a lecture document (.pptx/.pdf/.docx/.txt) | documents | W1 ✅ | [PENDING] | | |
| T5 | Adapt document; locate simplified text + explanation; play TTS audio; read the recommendation chip | adapt → audio → recommender | W1/W3 ✅ | [PENDING] | | |
| T6 | Ask the document a question; check cited sources | tutor RAG | W2 ✅ | [PENDING] | | |
| T7 | Create a task; get sprint plan; tick off sprints | EF coach | W2 ✅ | [PENDING] | | |
| T8 | Mock viva: answer questions using typing and/or Speak answer (voice consent permitting); confirm the session ends after exactly five questions | viva studio + voice loop | W2–3 ✅ | [PENDING] | | |
| T9 | Opt-in wellbeing check-in (low-mood path) + breathing exercise | check-in | W3 ✅ | [PENDING] | | |
| T10 | Export your data as JSON; delete interaction history | privacy suite | post-W3 ✅ | [PENDING] | | |

## 5. Quantitative results

### 5.0 Pre-session automated baseline (completed)

- **WCAG 2.2 AA static audit:** all text color pairs pass ≥ 4.5:1 contrast after palette remediation (measured range 5.09–5.72:1). Machine-rerunnable at any time via `backend/scripts/wcag_audit.py`, which regenerates `docs/accessibility/wcag-audit-machine-run.md`. Keyboard-only, NVDA screen-reader, and 400%-zoom reflow human passes remain **[PENDING]** — see `docs/accessibility/accessibility-checklist.md`.
- **Backend test suite:** 183 tests passing offline (no API key set), including graceful-degradation paths and hostile-key permutations; consent-denied requests verified to return calm 403s.
- **Frontend:** strict TypeScript production build green; vitest utility suite 11/11. Component/browser E2E automation does not exist yet — live-server smoke harnesses live at `backend/scripts/e2e_smoke*.py`; their re-run against the release build before sessions is **[PENDING]**.

### 5.1 System Usability Scale

Administered verbatim from `sus-survey.md`. **Target: mean ≥ 70** (spec §9).

| Participant | SUS score (0–100) |
|---|---|
| P1–P6 | [PENDING] |
| **Mean** | [PENDING] |

### 5.2 Task completion rates

[PENDING] — completion % per task; any task below 80% triggers redesign before submission.

## 6. Qualitative findings

Format: observation → evidence → severity → proposed change → status.

### 6.1 Content adaptation — [PENDING]
### 6.2 Onboarding, profiling, and consent experience — [PENDING]
### 6.3 Audio output (TTS, question playback, dictation) — [PENDING]
### 6.4 Accessibility and sensory comfort — [PENDING]
### 6.5 Trust, AI disclosure, and data rights — [PENDING]

## 7. Changes made in response

| Finding ID | Change shipped | Where |
|---|---|---|
| A1 (pre-session) | Calm-announcement pattern formalized: single polite live-region per page instead of assertive alerts (COGA-aligned rationale documented in audit method note) | all pages |
| A2 (pre-session) | Skip-to-content link added on every route | `App.tsx`, page `<main id="main">` |
| A3 (pre-session) | datetime deprecation removed from persistence layer | `models.py` |
| A4 (pre-session) | Text-pair contrast remediation across the token palette (all pairs now ≥ 4.5:1) | `styles/tokens.css` |
| [post-session rows] | [PENDING] | |

## 8. Limitations of this study

- Sample size 5–8 at one institution; directional, not generalizable.
- Moderator familiarity with participants (via EOC) may bias comfort ratings upward.
- If synthetic personas or community recruits are used (backup plan), §5–§6 and this section will disclose it explicitly.
- Automated audits cannot cover assistive-technology behavior — that is precisely what the pending human pass addresses.

## 9. Appendices

- A: `informed-consent-form.md`
- B: `sus-survey.md`
- C: Session logs / recording index — [PENDING]
- D: Automated WCAG report (`docs/accessibility/wcag-audit-report.md`) + machine-rerunnable script output (`wcag-audit-machine-run.md`)
