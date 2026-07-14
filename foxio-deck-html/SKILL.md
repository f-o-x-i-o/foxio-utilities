---
name: foxio-deck-html
description: Build a Foxio Design slide deck (pitch deck, studio-partner deck, capabilities overview) as a single self-contained HTML file that exports to a clean 16:9 PDF. Use whenever Simon asks to create, draft, or update a slide deck, presentation, or "deck" for Foxio Design — for design studios, direct clients, or any audience. Produces the same visual language as foxiodesign.com (near-black background, orange accent, Anton display type, JetBrains Mono body) using a container-query-based slide system that scales cleanly to any page size. Trigger on any mention of building slides, a pitch deck, a studio-partner deck, or turning a narrative into a presentation, even if the word "skill" is never used.
---

# Foxio Design — HTML Slide Deck Builder

Builds Foxio Design decks as a **single self-contained HTML file**: one `<section class="slide">` per slide, 16:9, styled with the Foxio visual system (near-black bg, `#F5821F` orange, Anton for display type, JetBrains Mono for everything else). Simon renders it to PDF himself (or via `assets/export_pdf.py`, see below).

The reference implementation lives in `assets/template.html` — an 11-slide skeleton with every reusable slide shape already built and commented, using `[BRACKETED]` placeholders instead of real copy. **Always start from the template, never rebuild the CSS from scratch.** It first proved itself as `FoxioDesign_StudioDeck_v2.pdf` (a pitch to industrial-design studios, July 2026) and was distilled into a generic skeleton from there.

---

## The core trick: `cqw`/`cqh` units

Every `.slide` has `container-type:size`, and all typography/spacing inside it is sized in `cqw`/`cqh` (1% of the slide's own width/height) instead of `vw`/`vh` or fixed px. That means:

- The whole deck scales proportionally at any zoom level or output size — no per-breakpoint media queries needed for the slide content itself.
- The only place a real pixel size shows up is `@page{size:1920px 1080px}` and the matching `.slide{width:1920px;height:1080px}` inside `@media print` — that's what fixes the *exported PDF's* physical page size. On screen, `.slide` sizes itself via `width:min(100vw, calc(100vh * 16/9))`.

Don't fight this system by introducing `px` or `vw` inside a slide's content — it'll break proportionality the moment the deck is rendered at a different size.

---

## Workflow

1. **Gather the narrative** — who's the audience, what's the one core claim, what proof exists (case studies, testimonials, numbers). If a chat thread already has this worked out (e.g. a positioning discussion), mine it instead of re-asking.
2. **Copy `assets/template.html`** to a working file, plus `assets/fonts/` and `assets/logo.png` alongside it (relative paths in the template assume they're siblings).
3. **Pick slides from the catalog below** — not every deck needs all 11. A short capabilities one-pager might use only slides 1, 3, 9, 11.
4. **Write real copy into each slide**, replacing the `[bracketed]` placeholders. Keep sentences short and concrete — this is a spoken/skimmed format, not a document. One idea per slide; resist the urge to add a second point to a slide that's already landed one.
5. **Drop in real photos** for any `.shotwrap img.shot` — the frame expects an image shown whole (no crop), so pick photos with reasonable aspect ratios up front rather than fighting `object-fit` after the fact.
6. **Render and check page breaks** (see Print verification below) before calling it done.

---

## Slide catalog (from `assets/template.html`)

| # | Shape | Use for |
|---|-------|---------|
| 1 | `glow` + `pad` + `foot` | Title / hook — one claim, signed by a person |
| 2 | `split` + `bars` | Problem — name the pattern, 2-3 failure modes as `.bar` blocks |
| 3 | `pad` + `flow` | Positioning — where you plug into the reader's existing process |
| 4 | `pad` + `rows` | Numbered process / workflow (3-5 steps) |
| 5 | `split` + photo, no list | Single-point argument — one idea, let the photo carry proof |
| 6 | `split` + `tech` grid | Capability grid, for a technical reader in the room |
| 7 | `split` + `stats` + `note` | Case study — named result with a scope callout |
| 8 | `cards` (quotes) | Social proof — 3 short verbatim testimonials |
| 9 | `cards` (offers) | Engagement tiers — smallest-risk option first |
| 10 | `split` + `econ` | Trust / economics — remove reasons to hesitate |
| 11 | `glow` + `hero` | Closing — payoff line + contact info |

Mix and reorder freely; these are shapes, not a fixed sequence. A deck can repeat a shape (e.g. two case-study slides) or skip most of them.

---

## Print verification (do this before delivering)

```bash
pip install playwright --break-system-packages -q
playwright install chromium
python3 assets/export_pdf.py path/to/deck.html path/to/deck.pdf
```

`export_pdf.py` renders via headless Chromium and honors the deck's own `@page{size:1920px 1080px}` rule (that's how `FoxioDesign_StudioDeck_v2.pdf` was produced — confirmed via `pdfinfo`: `Creator: HeadlessChrome`, `Producer: Skia/PDF`, page size `1440x810pt` = `1920x1080px`). Open the resulting PDF and check: no slide overflowing past its frame, no image stretched oddly, no orphaned heading. Fix in the HTML/CSS, not by hand-editing the PDF.

If Playwright isn't available (e.g. inside claude.ai's sandbox), the fallback is opening the HTML in Chrome and using Print → Save as PDF with the page size forced to match `@page` — same result, just manual.
