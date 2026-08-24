# Brief: docs-lead

Read `AGENTS.md` first. Spec lives at `docs/superpowers/specs/2026-08-21-sahaik-design.md`.

## Mission (Week 1)
Project documentation baseline for SIH submission.

## Ownership
`README.md`, `docs/architecture-diagram.md`, `docs/deployment-guide.md`, `docs/demo-video-script.md`, `docs/user-testing/user-testing-report-SKELETON.md`.

## Deliverables
1. README.md — project one-liner, problem statement ID, quickstart (backend venv commands + frontend commands from AGENTS.md), env vars table (GEMINI_API_KEY optional/graceful degradation noted, DATABASE_URL, JWT_SECRET), repo structure map, license MIT placeholder section, link to spec.
2. docs/architecture-diagram.md — Mermaid diagram(s): system context (React ↔ FastAPI ↔ LangGraph agents ↔ Gemini/TTS ↔ Postgres/SQLite), plus agent hub-and-spoke subgraph. Label week-1-implemented vs planned components.
3. docs/deployment-guide.md — local dev (exact commands), production sketch (uvicorn workers behind reverse proxy, static frontend hosting on Vercel/Netlify with VITE_API_BASE, Postgres DATABASE_URL swap, env var checklist), known limitations section.
4. docs/demo-video-script.md — 3-minute script, scene-by-scene table (timecode, screen, narration) opening on the pain point (dense slide wall) then register→onboarding→upload→adapt→audio payoff; accessibility statement beat included.
5. docs/user-testing/user-testing-report-SKELETON.md — structured skeleton (participants, procedure, tasks, SUS table placeholder, findings sections) referencing the consent form and SUS survey templates ux-lead authors.

## Style
No marketing fluff. Factual, judge-ready. Do not invent features beyond spec scope; mark unimplemented items clearly as "Planned".
