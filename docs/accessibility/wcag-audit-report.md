# WCAG 2.2 AA Audit Report — NEUROLEARN (static pass)

**Date:** 2026-08-23 · **Scope:** design tokens + routed pages (code-level audit; human passes pending)
**Method:** computed contrast ratios directly from the `:root` custom properties in `tokens.css` (WCAG relative luminance); structural checks against source.

## Contrast remediation (marigold brand color)

| Pair | Before | After |
|---|---|---|
| Marigold text on body background | 1.97:1 | **5.09:1** (#d9a441 → #855e12) |
| Marigold text on header composite | ~2.2:1 | **5.67:1** |
| Marigold text on surface / pressed-state white text | 1.97–2.21:1 | **5.72:1** |
| Pressed-state text if left dark-on-marigold | — | would be ~2.65:1 (flipped to #fffdf7) |
| Marigold on wash background | 1.97:1 | **4.70:1** |
| Focus-ring/bead accents on surface | <3:1 | **5.72:1** |

Additional fixes: removed an `opacity:.75` rule dragging muted text to 3.71:1 (now ≥4.7:1, up to 6.64:1 typical); `::selection` blend yields ≈8.27:1 over bg and ≈9.05:1 over surface; high-contrast mode remaps marigold (≥7.42:1 text pairs).

## Status

- All text-bearing token combinations now ≥ 4.5:1 (non-text UI ≥ 3:1). Cross-check: accessibility-checklist.md row 8 records marigold at 5.72:1.
- Machine-verifiable checks re-runnable via `backend/scripts/wcag_audit.py` (output: `wcag-audit-machine-run.md`).
- Keyboard-only golden path, screen-reader (NVDA), 320px/zoom reflow, and high-contrast OS-mode passes: **Pending human pass 2026-08** — not claimed here.
