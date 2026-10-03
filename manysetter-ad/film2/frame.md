# ManySetter — design spec (brand truth for the film)

Source: the app's compiled CSS (`../assets_in/app-css/app.css`) and manysetter.com.

## Palette

| Token | Hex | Use |
|---|---|---|
| ink-0 | #ffffff | cards, bubbles (lead) |
| ink-25 | #fdfcfb | light canvas |
| ink-50 | #faf9f8 | panels |
| ink-100 | #f5f3f2 | lead bubble fill on dark, inputs |
| ink-150 | #eeedeb | hairlines |
| ink-200 | #e6e5e3 | borders |
| ink-400 | #a3a09d | meta text |
| ink-500 | #76736f | secondary text |
| ink-600 | #585552 | body on light |
| ink-700 | #42403c | dimmed type on dark |
| ink-800 | #2a2825 | dark surfaces |
| ink-900 | #1a1816 | setter bubble, headlines |
| ink-950 | #0d0c0a | dark canvas |
| brand-50 | #fff7f2 | AI summary tint |
| brand-400 | #ff905e | glow core |
| brand-500 | #ff611d | accent, oval, dashed lines |
| brand-600 | #e64b15 | buttons, logo gradient end |
| brand-700 | #bc3a17 | links ("Why this reply?") |
| logo gradient | #ff884d → #e64b15 | logo tile only |
| emerald-500 | #00bb7f | success / Live / Learned |

One accent hue (orange). Neutrals are warm (tinted toward the accent). Shadows use #0d0c0a, never pure black.

## Type

- Display: Nohemi SemiBold (600), letter-spacing -0.045em, line-height 0.95.
- Subhead: Nohemi Medium (500).
- UI: Inter (variable), exactly as the app.
- Video scale: display 150–240px, titles 88–120px, UI zoomed 1.8–2.2x from app values.

## Components (app values at 1x)

- Card: radius 16–20px, white, shadow-card `0 0 0 1px #0d0c0a0f, 0 1px 2px #0d0c0a0a, 0 4px 12px -4px #0d0c0a0f`.
- Popover: shadow `0 0 0 1px #0d0c0a12, 0 4px 8px -2px #0d0c0a0f, 0 16px 36px -8px #0d0c0a29`.
- Bubble: radius 18px, tail corner 5px, padding 10px 14px, 14.5px Inter. Setter = ink-900/white (right). Lead = white with hairline (left).
- AI summary: radius 14px, bg brand-50 at 60%, inset ring orange at 22%.
- Secondary button: gradient ink-100 → ink-150, inset hairline + top highlight, radius 10px, height 36px.
- Primary button: brand gradient (brand-500 → brand-600), white text, inner top highlight.
- Chips: pill, 12px Inter medium, ink-100 bg; status dot 6px.
- Eyebrow chip: pill with hairline, orange 6px dot + label (site pattern).
- Hand-drawn oval: orange 3px stroke ellipse, slightly open, around the key word of a title.
- Dashed connectors: orange 2px, dash 6/6.
- Icons: Lucide, 2px stroke.

## Motion (from the app's CSS)

- ease-out-expo `cubic-bezier(.16,1,.3,1)` — arrivals.
- ease-spring `cubic-bezier(.34,1.36,.64,1)` — chips, toggles, flips.
- ease-drawer `cubic-bezier(.32,.72,0,1)` — camera glides, line draws.
- Mesh gradient blobs drift slowly (22–32s cycles in the app).

## Do / Don't

- Do: warm cream canvas with orange mesh glow; dark acts on ink-950 with a localized orange glow; generous negative space; real UI.
- Don't: gradient text, neon, purple/blue, pure black/white, full-screen linear gradients on dark, screenshots, stock imagery, outcome numbers.
