# Brief: frontend-lead

Read `AGENTS.md` first — it is law (ownership, contracts, style).

## Mission (Week 1)
Build the React SPA vertical slice: register/login → profiler onboarding wizard → document library with upload → document view rendering simplified text + audio player.

## Stack & constraints
- React 18 + Vite + TypeScript, react-router-dom. No other deps.
- You own `frontend/src/**` EXCEPT `src/styles/**` and `src/context/SensorySettings.tsx` (ux-lead's).
- ux-lead's exports exist per contract in AGENTS.md ("Frontend internal contracts") — import them even though they are being written concurrently; wrap the app in `SensorySettingsProvider`.
- Fetch wrapper in `src/lib/api.ts`: attaches Bearer token from `localStorage["sahaik_token"]`; base URL `import.meta.env.VITE_API_BASE || "http://localhost:8000"`.
- Entry: `src/main.tsx` renders `<App/>` inside router + provider; wire `import "./styles/tokens.css"` there.

## Pages (routes)
- `/login` and `/register` (forms, error display, store token+user, redirect `/onboarding` if profile incomplete else `/library`)
- `/onboarding` — multi-step wizard (~6 steps) collecting every LearnerProfile v1 field; PUT /api/profile; finish → onboarding_complete:true → /library. Progress indicator, one question per screen, plain language.
- `/library` — upload dropzone/file input (.pptx/.pdf/.docx/.txt), list documents from GET /api/documents, click through to detail; delete button.
- `/document/:id` — "Adapt" button calls POST /api/documents/{id}/adapt {formats:["simplified_text","tts_audio"]}; render simplified text using profile typography prefs; `<audio controls>` for tts_audio content URL; show explanation strings.

## Accessibility requirements (hard)
Semantic landmarks, labeled inputs (htmlFor/id), keyboard operable, visible focus, aria-live for async status messages, no auto-play of audio unless profile.audio_autoplay.

## Verify before reporting
1. `cd frontend && npm run build` passes type-check + build.
2. All four pages coded; API paths match AGENTS.md contract exactly.
Report: files created, build result, any contract gaps you had to assume around.
