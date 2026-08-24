# SahAIk — SIH 2026 Pitch Deck Outline (10 slides)

> Slide-by-slide content for the judging presentation. Each slide lists the headline, body beats, and the visual to show. Total speaking time: 7 minutes + 3-min demo video fallback.

## Slide 1 — Hook
**Headline:** "Dense slides. Timed labs. Viva anxiety. Built for a brain that works differently."
- Open with USAR's own pain points (from the problem statement, verbatim)
- Visual: wall-of-text slide vs SahAIk's simplified rendering, side by side

## Slide 2 — Problem
**Headline:** "Ed-tech assumes one kind of learner."
- ADHD/ASD/Dyslexia/Dyspraxia/SPD students face tools designed for neurotypical patterns
- India gap: RPwD Act mandates support; implementation is thin; existing tools are Western, expensive, single-purpose (Brain in Hand £1,550/yr; Glean = notes only)
- Visual: competitive landscape table from spec §2.3

## Slide 3 — Solution
**Headline:** "SahAIk: one companion that adapts everything to your profile."
- Upload lecture → simplified text / audio / structure, tuned to your sensory-cognitive profile
- Tutor that answers only from YOUR material · assignments → sprints · mock vivas · wellbeing check-ins
- Visual: architecture diagram (docs/architecture-diagram.md)

## Slide 4 — How it works
**Headline:** "Agentic, multimodal, grounded."
- LangGraph hub-and-spoke agents sharing one LearnerProfile
- Retrieval grounded in uploaded chunks (embeddings when keyed, TF-IDF offline) — answers cite sources
- Voice loop: browser STT + TTS playback of questions
- Visual: ask-flow sequence diagram

## Slide 5 — Personalization engine
**Headline:** "It learns how YOU learn — and tells you why."
- Profiler onboarding → modality/chunk/pace/sensory preferences
- Recommender blends profile rules + interaction history ("You chose audio 3 times before…")
- Every rendering ships an explanation string
- Visual: DocumentView recommendation chip screenshot

## Slide 6 — Ethics by design ⭐ differentiator
**Headline:** "No surveillance. No dark patterns. Ever."
- Self-report wellbeing first; NO camera-based emotion recognition (cite IEEE TAFFC / AI & Ethics critiques we heeded)
- Opt-in voice/telemetry/memory; export & delete; plain-language AI disclosure
- Calm-UI announcements (COGA-aligned) instead of jarring alerts
- Visual: consent toggles UI + ethics stance quote

## Slide 7 — Accessibility
**Headline:** "WCAG 2.2 AA is our floor, not our ceiling."
- Computed contrast 5/5 pass (13.9:1 body); dyslexia-friendly typography mode; reduced-motion everywhere
- Skip-links, labeled controls, keyboard-first, screen-reader-ready live regions
- Accessibility-first build: static WCAG audit passing; human keyboard/NVDA/zoom validation and EOC-guided user testing scheduled before submission
- Visual: audit report summary + sensory settings panel

## Slide 8 — Engineering rigor
**Headline:** "183 tests. 53 endpoints. Zero-crash degradation."
- Full pytest suite green; typed strict frontend build green
- Every LLM feature falls back gracefully without an API key (`used_llm: false` + heuristic paths)
- Docker deployment story; SQLite→Postgres path documented
- Visual: test/CI summary table

## Slide 9 — Impact & roadmap
**Headline:** "From one lab in East Delhi to every HEI in India."
- Now: content adaptation, tutor, EF coach, viva studio, wellbeing
- Next: pgvector semantic retrieval at scale, Hindi/Indic TTS voices, EOC dashboard, campus pilot with counselling services
- Dataset plan: RAVDESS/TORGO-informed speech work, consented user feedback loops
- Visual: roadmap timeline

## Slide 10 — Team & close
**Headline:** "Built with neurodivergent students, not just for them."
- Six-member team + role map; EOC partnership; demo video link; repo/docs links
- Close on a participant quote placeholder from testing report §6

---
**Judge-question prep anchors:** ethics stance (§6), why TF-IDF now/pgvector next (§4), graceful degradation proof (§8), co-design evidence trail (§7).
