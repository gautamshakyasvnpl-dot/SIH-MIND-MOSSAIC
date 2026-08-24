# Demo Video — Production Checklist

Script: `docs/demo-video-script.md` (3-minute scene table). This checklist gets you from script to rendered file.

## Pre-production
- [ ] Fresh demo database (`Remove-Item sahaik.db`), seeded with one clean lecture PPTX/PDF (photosynthesis sample from `backend/tests/fixtures` strategy)
- [ ] Backend running: `backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --port 8000`
- [ ] Frontend running: `cd frontend; npm run dev` (port 5173)
- [ ] Browser at 100% zoom, bookmarks bar hidden, dark theme OFF (tokens are light-theme), screen recorder at 1080p/30fps minimum
- [ ] Microphone level checked for narration; captions/subtitle track planned (accessibility of the video itself)

## Shot list (maps to script scenes)
| Scene | Screen | Action | Duration |
|---|---|---|---|
| 1 Hook | static slide wall | dense unreadable slide full-screen | 0:00–0:15 |
| 2 Register | /register | type email/name, submit | 0:15–0:35 |
| 3 Onboarding | /onboarding | click through 3 choices incl. dyslexia font — font visibly changes | 0:35–1:00 |
| 4 Upload | /library | pick sample.pptx, upload, list refreshes | 1:00–1:20 |
| 5 Adapt | /document/:id | click Adapt → simplified text + explanation appears; press play on audio | 1:20–1:50 |
| 6 Ask | same page | type "What captures sunlight?" → grounded answer + sources visible | 1:50–2:10 |
| 7 Viva | /document/:id/viva | start, Listen to question audio, answer ×2, feedback + score shown | 2:10–2:35 |
| 8 Wellbeing | /wellbeing | low-mood check-in → suggestion + breathing steps | 2:35–2:50 |
| 9 Close | ethics card | consent toggles + "no camera surveillance" statement + repo link | 2:50–3:00 |

## Recording tips
- Record each scene separately; cut mistakes in edit (no live-typing fumbles)
- Zoom browser to 110% for readability on projectors
- Keep cursor movements slow and deliberate
- Narration follows the script table verbatim; add 1-second pauses at scene cuts

## Post-production
- [ ] Captions burned in or .srt attached (accessibility deliverable)
- [ ] Background music off or ≤ -20dB under narration (noise-sensitive viewers — practice what we preach)
- [ ] Export 1080p MP4 (H.264), target < 150 MB
- [ ] Filename: `SahAIk_Demo_SIH2026.mp4`
