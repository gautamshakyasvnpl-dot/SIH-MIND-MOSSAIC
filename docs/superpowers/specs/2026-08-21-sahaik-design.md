# SahAIk — AI-Powered Inclusive Learning & Wellbeing Platform for Neurodivergent Learners

**Competition:** Smart India Hackathon 2026 (Official Entry)
**Problem Statement:** GGSIPU2605 — AI-Powered Inclusive Learning & Wellbeing Platform for Neurodivergent Learners
**Organization:** University School of Automation & Robotics (USAR), GGSIPU East Delhi Campus
**Theme:** Inclusive Education, Accessibility & Digital Health
**Version:** 1.0 · **Date:** 2026-08-21 · **Status:** Approved for implementation planning

---

## 1. Problem Statement Analysis

Neurodivergent individuals — including those with ADHD, Autism Spectrum Disorder (ASD), Dyslexia, Dyspraxia and Sensory Processing Disorders (SPD) — encounter educational technologies designed for neurotypical learning patterns. In a higher-education setting such as USAR, GGSIPU, this manifests concretely as:

- Dense lecture slides and reading material
- Timed lab assessments that penalize processing-speed differences rather than conceptual understanding
- Group-project coordination friction
- Viva and presentation anxiety
- Noisy laboratory environments (sensory overload)
- Examination formats that reward speed over understanding

The PS requires an AI-powered platform that adapts educational content, communication, emotional support and creative workflows to each learner's cognitive and sensory profile — with accessibility-first design, continuous learning from interactions, privacy, explainability, and co-design with the university's Equal Opportunity Cell / counselling services under informed consent.

### 1.1 Scoping decision: four PS pillars

| Pillar | Role in SahAIk |
|---|---|
| Adaptive content | Core spine — the Adapter engine |
| Assistive communication | Flagship demo — Viva Coach + voice-first interaction |
| Emotional wellbeing | Opt-in companion module (self-report first) |
| Executive function | Sprint Coach + group-project board |

**Positioning statement:** *SahAIk is the first integrated, agentic, multimodal inclusive-learning platform built for neurodivergent higher-education students in India.*

---

## 2. Research Findings

### 2.1 Domain evidence (2024–2026)

- **OECD (Feb 2026), "AI to Support Neurodivergent Learners in VET":** highest-leverage AI applications are adaptivity, text-to-speech/speech-to-text, and generative AI; commercial "hyperpersonalization" remains unrealized. Learners already self-assemble to-do lists, reminders, and video supports.
- **Choi et al. (ACM CHI 2024):** autistic adults already use LLMs to decode social norms, draft emails, navigate bureaucracy, and manage executive tasks — validates LLM-based communication assistance for daily independence.
- **Das Deep et al. (2025–26):** AI-based systems enhanced academic writing, self-regulation and executive functioning in college students with ADHD; real-time personalized feedback outperformed traditional tutoring.
- **Gharaibeh & Basulayim (2025); Elfateh et al. (IEEE AICT 2025):** LLM-based instruction significantly improved reading comprehension for dyslexic learners; post-ChatGPT assistive platforms go beyond plain TTS toward adaptive tutoring.
- **Scoping review (Computers & Education: AI, Dec 2025):** GenAI shows strong promise for neurodivergent learners but coverage in *higher education* is thin; cognitive-offloading is a documented risk → design principle: scaffold skill-building (Socratic modes), never answer-vending.

### 2.2 India context

- **eLife (2024), "Navigating neurodiversity in higher education in India" (Taneja, Viswanathan, Rajan):** Indian HE remains deficit-focused; RPwD Act 2016 recognizes specific learning disabilities and autism and mandates institutional support via Equal Opportunity Cells, but implementation is weak (~5% reservation poorly enforced). The paper explicitly recommends co-creation with neurodivergent students — mirroring the PS requirement.
- Regulatory anchors: RPwD Act 2016; UGC PwD guidance for HEIs; DEPwD "Accessibility Guidelines and Standards for Higher Education Institutions" (June 2024).
- Localization: English + Hindi UI strings; Indic-capable TTS voices.

### 2.3 Competitive gap analysis

| Existing product | Scope | Gap SahAIk exploits |
|---|---|---|
| Brain in Hand (UK) | Routine planning + human coaching, £1,550/yr | Not AI-native; no learning-content adaptation; unaffordable/irrelevant for Indian HEIs |
| Cognassist | Cognitive-mapping assessment + workplace strategies | Assessment only; does not adapt actual course material |
| Glean / Jamworks | Lecture capture & note-taking | Single-purpose; no wellbeing or executive-function integration |
| EzDucate / Booost "Luna" | K-12-oriented AI study aids | Not higher-ed; not multimodal or agentic |

**No existing product offers an integrated, agentic, multimodal platform for neurodivergent higher-ed students localized for India.**

### 2.4 Ethics finding (design-critical)

Classroom facial-expression recognition (FER) is academically contested:

- Banzon, Beever & Taub (IEEE TAFFC 2023): FER data collection in classrooms argued not ethically appropriate outside controlled research; recommends curtailing applied use.
- *AI & Ethics* (Springer, Dec 2025): emotion-AI classroom monitoring raises consent, bias, cultural-misreading, and surveillance risks.

**Design decision:** emotional support is **self-report check-ins first**; voice-tone analysis secondary; **camera-FER absent by default**; everything opt-in; all personal data exportable/deletable; plain-language AI disclosure; no dark patterns. This stance is documented and presented at judging as evidence of ethical maturity.

---

## 3. System Architecture

```
┌────────────────────────── React Web App (WCAG 2.2 AA + W3C COGA) ──────────────────────────┐
│  Sensory Settings Panel │ Doc Library │ Coach Chat │ Sprint Board │ Viva Studio │ Check-in  │
└──────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                       │ REST/WebSocket
┌────────────────────────────── FastAPI Backend ─────────────────────────────────────────────┐
│  Auth (Firebase/JWT) │ Consent & Privacy Layer │ Telemetry (opt-in) │ Explainability API   │
│  ┌────────────────────── LangGraph Agent System ──────────────────────┐                    │
│  │ Orchestrator (Coach, hub-and-spoke, shared LearnerProfile state)   │                    │
│  │ ├─ Profiler      → cognitive/sensory preference profile (NOT diagnosis)                │
│  │ ├─ Adapter       → PPTX/PDF/DOCX → simplified text · chunks · concept maps · TTS audio │
│  │ ├─ Tutor         → RAG Q&A grounded in uploaded material (pgvector)                    │
│  │ ├─ EF Coach      → task breakdown, sprint timers, nudges, group-project board          │
│  │ ├─ Viva Coach    → mock viva w/ voice, adaptive pacing, feedback                       │
│  │ └─ Wellbeing     → opt-in check-ins, grounding exercises, EOC escalation info          │
│  └────────────────────────────────────────────────────────────────────┘                    │
│  PostgreSQL + pgvector │ Gemini API (primary LLM) │ Whisper STT │ TTS                      │
└────────────────────────────────────────────────────────────────────────────────────────────┘
ML differentiators: Whisper+LoRA fine-tuned on TORGO (atypical-speech tolerance, timeboxed)
· RAVDESS voice-emotion classifier (opt-in research module) · modality recommendation engine
(profile + interaction telemetry → format ranking with explanations)
```

### 3.1 Agent specifications

All agents read/write a shared typed `LearnerProfile` state object; only the Orchestrator coordinates between them (hub-and-spoke; no agent-to-agent calls). Every agent response includes an `explanation` field surfaced in UI where relevant.

1. **Profiler** — Onboarding questionnaire + ongoing interaction signals → preference profile: modality affinity (text/audio/visual), preferred chunk size, typography/spacing flags, sensory flags (motion/audio), pacing. Explicitly *not* a diagnosis; plain-language consent at every step.
2. **Adapter** — Ingests PPTX/PDF/DOCX/plain text → profile-conditioned outputs: simplified text (vocabulary/length control), chunked summaries, Mermaid concept maps, dyslexia-friendly rendering hints (font, spacing, line length), TTS audio files.
3. **Tutor** — Retrieval-augmented Q&A grounded strictly in the student's uploaded material (pgvector). Socratic protocol: guides with questions before revealing answers; never dumps answers unprompted.
4. **EF Coach (Executive Function)** — Breaks assignments into sprints with timers; deadline nudges calibrated to time-blindness; shared group-project task board with role clarity.
5. **Viva Coach** — Generates mock viva questions from uploaded material; full voice loop (Whisper STT + TTS); adaptive pacing (pauses, rephrasing, one-question-at-a-time); post-session structured feedback; question difficulty escalates gently to build tolerance for real vivas.
6. **Wellbeing Companion** — Opt-in mood check-ins (emoji/scale/journal), grounding exercises (box breathing, 5-4-3-2-1), pre-viva calming routines; surfaces EOC/counselling contact and escalation paths. Crisis-safe guardrails: no diagnosis, referral-first language, no dependency loops.
7. **Orchestrator (Coach)** — Routes intents across agents; maintains session + long-term memory of preferences; exposes explainability ("why am I seeing this format?").

### 3.2 Data model (core tables)

`users` · `consents` · `learner_profiles` (JSONB preferences) · `documents` (+ extracted text) · `chunks` (+ pgvector embeddings) · `adaptations` (document × format × user rating) · `sprints` / `tasks` · `viva_sessions` / `viva_turns` · `checkins` · `telemetry_events` (opt-in) · `recommendation_log`.

Privacy rules: telemetry and voice features are opt-in; every table with user data supports export and cascade delete; embeddings derived from user documents are deleted with the document.

### 3.3 Privacy, consent & explainability commitments

- Granular consent toggles per feature (voice, telemetry, memory).
- Plain-language AI disclosure on every agent surface ("You are talking to an AI coach").
- Data export (JSON) and account/data deletion endpoints.
- Explainability API: every adaptation/recommendation returns a human-readable reason string shown in UI.
- No dark patterns: equal-friction accept/decline, no nudges toward enabling surveillance features.

---

## 4. ML Components & Datasets

| Component | Dataset(s) | Approach | Status |
|---|---|---|---|
| Atypical-speech-tolerant STT | TORGO (HuggingFace `abnerh/TORGO-database`, ~16.6k utterances) | Whisper + LoRA fine-tune | Timeboxed stretch goal (3 days max); fallback = stock Whisper + always-available text input |
| Voice-emotion classifier | RAVDESS (7,356 clips, 8 emotions) | CNN/transformer audio classifier behind opt-in toggle | Research module, demo-grade acceptable |
| Modality recommender | User's own telemetry (opt-in) + profile | Rule-based v1 → contextual bandit v2 | Ships with explanation strings |
| Engagement analytics (optional) | DAiSEE | Deferred unless time permits | Not required |

Open Educational Resources seed the demo library so judges see real lecture-style inputs without needing their own files.

## 5. Accessibility Compliance Plan

- Target: **WCAG 2.2 AA**, verified by automated audit (axe/Lighthouse) + manual keyboard/screen-reader passes.
- Beyond WCAG (cognitive layer): W3C *Making Content Usable for People with Cognitive and Learning Disabilities* (COGA); Neurodiversity Design System patterns; UK Gov dos/don'ts posters.
- Concrete UI guarantees: sensory settings panel (reduced motion, audio off by default, font/spacing controls, high-contrast themes, one-thing-at-a-time layouts), consistent navigation, progress indicators on multi-step flows, plain-language error messages, no auto-playing media, no time pressure without explicit extension options.
- RPwD Act 2016 alignment noted in technical documentation.

## 6. Deliverables Mapping (all 9 PS items)

| PS Deliverable | Artifact |
|---|---|
| Functional AI application | Deployed web application |
| Accessible User Interface | WCAG 2.2 AA audit report + sensory settings panel |
| Personalized Recommendation Engine | Modality recommender + explanation UI |
| Technical Documentation | `/docs` architecture + API reference |
| Source Code | Monorepo, MIT license |
| Demo Video | 3-minute scripted walkthrough (opens on Viva Studio scene) |
| User Testing Report | Co-design sessions with EOC + 5–8 neurodivergent students; SUS target ≥ 70; qualitative findings |
| Architecture Diagram | Polished diagram (draw.io/Excalidraw export) |
| Deployment Guide | Docker Compose + Cloud Run/Vercel runbook |

## 7. Team of 6 — Ownership

1. **Frontend lead** — React app, accessibility patterns, sensory panel
2. **Backend lead** — FastAPI, PostgreSQL/pgvector, auth, consent layer
3. **Agents lead** — LangGraph system, prompts, RAG pipeline
4. **ML lead** — Whisper LoRA fine-tune, RAVDESS classifier, recommender
5. **UX/Accessibility lead** — design system, WCAG audits, EOC/tester recruitment coordination
6. **Docs/Pitch lead** — demo video, user-testing report, deployment guide, pitch deck

## 8. Four-Week Execution Plan

| Week | Goal | Exit checkpoint |
|---|---|---|
| 1 | Vertical slice: auth → profiler onboarding → upload PPTX/PDF → simplified text + TTS output. Begin tester recruitment. | Working end-to-end demo path |
| 2 | Tutor RAG + EF Coach + Viva Coach (text mode) | **Feature freeze** end of week |
| 3 | Voice loop (STT/TTS), wellbeing check-ins, recommender + explanations, accessibility polish | Full feature set integrated |
| 4 | Integration tests, user-testing sessions, WCAG audit, demo video, docs, deployment runbook, pitch deck buffer | Submission-ready |

## 9. Testing & Evaluation Strategy

- **Unit/integration:** pytest for API; LangGraph node-level tests with stubbed LLM calls; Playwright smoke tests for critical flows.
- **User testing:** 5–8 participants recruited via Equal Opportunity Cell / counselling services (informed consent forms prepared in plain language); System Usability Scale questionnaire (target ≥ 70); task-completion rates on three golden paths (upload→adapt, viva practice, check-in).
- **Accessibility:** axe-core automated scans in CI; manual NVDA/VoiceOver pass; contrast checks.
- **Backup recruitment** if campus recruitment stalls: neurodivergent-led online communities and clearly-labeled synthetic personas (disclosed in the report).

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Scope creep | Feature freeze end of Week 2; vertical slice first |
| Gemini quota/cost limits | Response caching; fallback free-tier model; batch TTS |
| TORGO fine-tune overrun | Hard 3-day timebox; stock Whisper fallback shipped regardless |
| Tester recruitment delay | Start Week 1; backup communities/personas plan |
| Ethical misreading of wellbeing/FER features | Published ethics stance (§2.4, §3.3) presented proactively at judging |

## 11. Key References

1. OECD (2026). *AI to Support Neurodivergent Learners in Vocational Education and Training.*
2. Choi et al. (CHI 2024). LLM use by autistic adults for daily independence.
3. Das Deep et al. (2025–26). AI systems for executive functioning in ADHD college students.
4. Taneja, Viswanathan & Rajan (eLife 2024). Navigating neurodiversity in higher education in India.
5. Banzon, Beever & Taub (IEEE TAFFC 2023). Facial Expression Recognition in Classrooms: Ethical Considerations.
6. *AI & Ethics* (Springer 2025). Emotion AI in the classroom: ethics of monitoring student affect.
7. W3C. WCAG 2.2; *Making Content Usable for People with Cognitive and Learning Disabilities* (COGA).
8. Neurodiversity Design System (neurodiversity.design); UK Gov accessibility dos/don'ts posters.
9. Datasets: TORGO (Univ. of Toronto / Holland-Bloorview), RAVDESS (Zenodo), FER-2013 (Kaggle), DAiSEE.
10. RPwD Act 2016; DEPwD Accessibility Guidelines for Higher Education Institutions (2024).

---

*Next step: invoke writing-plans skill to produce the detailed implementation plan before any code.*
