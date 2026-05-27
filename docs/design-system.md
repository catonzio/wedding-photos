# Wedding Photos — Design System

> Style: Minimalist botanical · Palette: White / Gold / Sage green

---

## Color Palette

| Token | Hex | Usage |
| --- | --- | --- |
| `--color-bg` | `#F8F7F2` | Page background (warm off-white) |
| `--color-surface` | `#FFFFFF` | Cards, panels, drawer |
| `--color-text` | `#2D2C28` | Primary text (warm near-black) |
| `--color-text-muted` | `#7C7B72` | Secondary text, captions |
| `--color-gold` | `#B8972E` | Accents only — dividers, dots, borders on focus |
| `--color-gold-light` | `#E8D9A0` | Gold at low opacity — subtle fills |
| `--color-sage` | `#7A9069` | Sage green — tags, active states |
| `--color-sage-light` | `#E4EAE0` | Very light sage — card backgrounds, hover states |
| `--color-border` | `#E2E0D6` | Borders, dividers (warm grey) |

**Rule:** Gold is used sparingly — only as a decorative accent, never as a fill on large areas. Sage is the primary brand color.

---

## Typography

Load from Google Fonts:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Jost:wght@300;400;500&display=swap" rel="stylesheet">
```

| Role | Font | Weight | Notes |
| --- | --- | --- | --- |
| Page title (h1) | Cormorant Garamond | 300 italic | Large, airy, romantic |
| Section heading (h2) | Cormorant Garamond | 400 | For table names |
| Sub-heading (h3) | Cormorant Garamond | 300 | For descriptions |
| Body text | Jost | 400 | All prose, descriptions |
| Labels / nav | Jost | 500 | Uppercase, tracked |
| Captions / muted | Jost | 300 | Photo captions, counts |

**Scale (mobile):**

- h1: `2.25rem` / line-height `1.1`
- h2: `1.75rem` / line-height `1.2`
- Body: `1rem` / line-height `1.7`
- Label: `0.75rem` / letter-spacing `0.12em` / uppercase

---

## Layout

- **Max width:** `480px` — centered on larger screens, full-width on mobile
- **Page padding:** `1.25rem` horizontal
- **Safe areas:** respect `env(safe-area-inset-*)` for notched phones

```css
.page-container {
  max-width: 480px;
  margin: 0 auto;
  padding: 0 1.25rem;
  padding-bottom: env(safe-area-inset-bottom, 1rem);
}
```

---

## Components

### Navigation Bar

- Height: `56px`
- Background: `--color-surface` with `border-bottom: 1px solid --color-border`
- Left: hamburger icon (opens drawer) — sage green on tap
- Center: app title in Cormorant Garamond 300 italic, `1.1rem`
- Right: empty or subtle leaf SVG decoration
- Sticky at top, `backdrop-filter: blur(8px)` with slight transparency when scrolled

### Side Drawer (menu)

- Slides in from left, `width: 85vw`, max `360px`
- Overlay: `rgba(45,44,40,0.4)` behind it
- Header: couple's name + date in Cormorant italic
- List of tables: cover photo thumbnail (48×48, rounded) + table name
- Active table highlighted with sage-light background + left border in sage
- Transition: `transform 300ms cubic-bezier(0.4, 0, 0.2, 1)`

### Table Card (menu page)

- Aspect ratio `4:3` cover photo, full bleed
- Below: table name in Cormorant 400, `1.1rem`
- Subtle `box-shadow: 0 1px 4px rgba(0,0,0,0.08)`
- Border: `1px solid --color-border`
- Tap: slight scale down `0.97` with transition `150ms`
- Grid: 2 columns on mobile, `gap: 1rem`

### Carousel (table page)

- Full-width (edge to edge, no page padding)
- Photos: `aspect-ratio 4:3`, `object-fit: cover`
- Videos: same aspect ratio, native controls
- Pagination: gold dots below (`--color-gold`, inactive: `--color-gold-light`)
- Swipe: Swiper.js with `loop: false`, `spaceBetween: 0`
- Counter: `3 / 12` in Jost 300 top-right corner, semi-transparent white

### Decorative Divider

A thin horizontal rule with a small leaf/branch SVG centered:

```text
——— 🌿 ———
```

Implemented as: `1px solid --color-border` with a centered inline SVG. Used to separate carousel from description, and section headers on the menu page.

### Denied Page

- Centered vertically and horizontally
- Small botanical SVG illustration (simple branch)
- Text in Cormorant 300 italic: *"Questa pagina è riservata agli invitati"*
- No error codes, no hints about tokens
- Background: `--color-bg`, same as rest of the app

---

## Motion & Animation

Keep animations subtle and purposeful:

| Element | Animation |
| --- | --- |
| Drawer open/close | `transform: translateX` · `300ms ease` |
| Card tap | `transform: scale(0.97)` · `150ms` |
| Page load | `opacity: 0 → 1` · `400ms ease` (CSS only, no JS) |
| Carousel swipe | Swiper.js default (momentum-based) |
| Overlay | `opacity 300ms` |

No bounce, no parallax, no heavy motion. The app should feel calm and elegant.

---

## Icons

Use **Heroicons** (MIT, via CDN or inline SVG) for:

- Hamburger menu (3 lines)
- Close (×)
- Back arrow (←)

Stroke width: `1.5` (thin, refined). Color: `--color-text` or `--color-sage`.

---

## Photo & Video Guidelines

For best visual result on the day:

- **Photos:** JPEG, max 1500px on the long side, quality 85. Use `loading="lazy"`.
- **Videos:** MP4 (H.264), max 720p, `preload="metadata"` (not auto).
- **Cover images:** Square crop preferred, or 4:3. Load eagerly (`loading="eager"`).
- The QR code representative photo printed at the table should match the `cover` field.
