# Accessibility Checklist — WCAG 2.2 AA

Pages audited: `/` (landing), `/login`, `/register`, `/onboarding`, `/dashboard`, `/library`, `/document/:id`, `/tasks`, `/document/:id/viva`, `/wellbeing`

**Method legend:** `static` = verified in source/CSS on 2026-08-23; `computed` = contrast ratio from WCAG relative-luminance formula over `tokens.css` values (2026-08-23); `human` = requires a live person + device/AT.

| # | Criterion | How implemented / verified | Method | Status |
|---|---|---|---|---|
| 1 | 1.1.1 Non-text Content | Decorative marks (`स`, squiggle, beads) `aria-hidden`; no `<img>` without alt anywhere in src | static | ✅ |
| 2 | 1.3.1 Info and Relationships | Semantic landmarks (`header nav main footer`), `fieldset/legend` groups, `label htmlFor` on every input (pattern-checked across all pages/components) | static | ✅ |
| 3 | 1.3.5 Identify Input Purpose | `autocomplete="email" / "current-password" / "new-password" / "name"` present in Login/Register | static | ✅ |
| 4 | 1.4.3 Contrast (Minimum) | Body #29241c on #f6efe2 = **13.47:1**; on surface #fffdf7 = **15.14:1**; links #9c4a1f on bg = **5.38:1**; button text #fffdf7 on primary #9c4a1f = **6.05:1**, on accent #3e6050 = **6.90:1**; marigold text remediated #d9a441→#855e12 (see report) — all pairs ≥ 4.5:1 | computed | ✅ |
| 5 | 1.4.4 Resize Text | Relative units only (rem/em/clamp), single-column flow — static reasoning passes; actual zoom behavior unverified | static + human | ⏳ Pending human pass 2026-08 |
| 6 | 1.4.10 Reflow at 320px | CSS audit: all containers flex-wrap/max-width %, inputs `min(…, 100%)`; ≤480px media query converts header nav to 2-col grid, no fixed widths > viewport; real-device pass not yet done | static + human | ⏳ Pending human pass 2026-08 |
| 7 | 2.1.1 Keyboard | All controls native `<button>/<a>/<input>/<select>`; no pointer-only handlers (pattern-checked). Golden-path keyboard walkthrough not yet run | static + human | ⏳ Pending human pass 2026-08 |
| 8 | 2.4.7 Focus Visible | Global `:focus-visible { outline: 3px solid var(--color-primary); outline-offset: 2px }`; input focus ring marigold #855e12 = 5.72:1 vs adjacent surface (≥3 required for non-text) | static + computed | ✅ |
| 9 | 2.5.8 Target Size (Min) | Buttons ≈ 50px tall (17px × 1.65 line-height + 21.6px block padding); ≤480px nav items enforce `min-block-size: 44px`. Touch ergonomics unverified | static + human | ⏳ Pending human pass 2026-08 |
| 10 | 3.2.3 Consistent Navigation | Single shared `SiteHeader` component rendered on every authenticated route | static | ✅ |
| 11 | 3.3.1 Error Identification | Errors rendered in `role="alert"` near forms (pattern-checked) | static | ✅ |
| 12 | 3.3.2 Labels or Instructions | Every control labeled; upload accepted-formats stated in label | static | ✅ |
| 13 | 3.3.7 Redundant Entry | Profile persisted server-side; onboarding shows review step before save | static | ✅ |
| 14 | 4.1.3 Status Messages | Upload/adapt/viva status via `role="status"` polite live regions (App + page level) | static | ✅ |
| 15 | COGA: one-thing-at-a-time | Onboarding = one question per screen with progress beads | static | ✅ |
| 16 | COGA: plain language | Copy intended jargon-free; plain-language review is human judgment | human | ⏳ Pending human pass 2026-08 |
| 17 | Motion sensitivity | `[data-motion="reduced"]` kill-switch block AND `@media (prefers-reduced-motion: reduce)` both zero out transitions/animations | static | ✅ |
| 18 | Dyslexia-friendly mode | `[data-font="dyslexia_friendly"]` switches family + letter-spacing 0.03em + word-spacing 0.14em | static | ✅ |
| 19 | High-contrast mode | `[data-contrast="high"]` remaps palette incl. marigold #6f500c = 7.42:1 on white; noise texture hidden | static + computed | ✅ |
| 20 | No autoplay surprise | `<audio controls preload="none">`; autoplay only when profile `audio_autoplay` true | static | ✅ |

## Manual pass pending (requires human session) — Pending human pass 2026-08
- Screen reader walkthrough (NVDA + Chrome) of register → onboarding → upload → adapt flow
- Keyboard-only run of full golden path
- Zoom 400% spot-check and 320px physical-device reflow check
- Plain-language / cognitive-load copy review
- Touch-target ergonomics on a real phone

**Status:** static + computed checks pass as of 2026-08-23; human audit scheduled per spec §9.
