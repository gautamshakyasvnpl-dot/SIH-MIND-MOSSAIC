# Brief: ux-lead

Read `AGENTS.md` first — it is law. Use installed skills `.agents/skills/wcag-accessibility-audit/SKILL.md` and local `web-design-guidelines` guidance while designing.

## Mission (Week 1)
Design system foundation + sensory settings infrastructure + accessibility documentation + user-testing instruments.

## Ownership
`frontend/src/styles/**`, `frontend/src/context/SensorySettings.tsx`, `docs/accessibility/accessibility-checklist.md`, `docs/user-testing/informed-consent-form.md`, `docs/user-testing/sus-survey.md`.

## Deliverables
1. `frontend/src/styles/tokens.css` — exact variable names from AGENTS.md; calm low-saturation palette (contrast ≥4.5:1 body text), generous spacing scale, radius tokens, focus-visible ring (≥2px, high contrast), `[data-font="dyslexia_friendly"]` (font-family switch to Atkinson Hyperlegible w/ fallback Verdana + letter-spacing 0.02em + word-spacing 0.12em), `[data-spacing="wide"]` (line-height ≥1.8), `[data-motion="reduced"]` (transition/animation durations ~0), `@media (prefers-reduced-motion)` equivalent, base reset (box-sizing, margin 0, min font-size 16px, max line length ~70ch on prose class).
2. `frontend/src/context/SensorySettings.tsx` — EXACT exports from AGENTS.md contract. SensoryPrefs type mirrors LearnerProfile display fields (font_style, line_spacing, reduce_motion, modality_affinity, audio_autoplay, chunk_size, pace, noise_sensitive). Persist localStorage "sahaik_sensory" (load-on-init, write-on-change), apply data attributes to document.documentElement, export types too.
3. Accessibility checklist doc mapped to WCAG 2.2 AA criteria with pass/fail columns for the four Week-1 pages (login/register/onboarding/library/document view).
4. Plain-language informed consent form template (for EOC-coordinated testing; includes purpose, data handling, withdrawal right, contact) + SUS survey template with scoring instructions.

## Constraints
Do NOT create page components or touch anything outside ownership. frontend-lead consumes your exports concurrently — match the contract character-for-character.

## Self-check
`tsc`-level sanity: your two frontend files should be syntactically valid TS/TSX on their own (they get compiled during integration build).
