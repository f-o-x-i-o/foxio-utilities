---
name: foxio-portfolio
description: Build a Foxio Design "Selected Work" portfolio PDF — a print-ready case-study document (A4, photo-led) showcasing past projects for a specific prospect or audience. Use whenever Simon asks to create, draft, or update a portfolio, case-study deck, or "show them the projects" document for Foxio Design. Handles the recurring hard part correctly by default: most of Simon's track record predates Foxio Design's 2026 founding and was done as an employee/contractor/freelancer for other companies, so every case needs an honest role+period attribution line, and some cases must be anonymized (no client name, no product name, board-level images only). Trigger on any mention of a portfolio, "send them examples of past work", a capabilities/case-study document, or adapting past-work materials for a specific lead.
---

# Foxio Design — Selected Work Portfolio Builder

Builds a photo-led, A4-portrait case-study PDF: one cover, one intro/stats page, one full page per featured case, a compact "more selected work" page for smaller cases, and a closing "how we work + contact" page. Visual language matches foxiodesign.com — near-black/white/orange, Anton for display type, JetBrains Mono for labels and body, section labels prefixed `//` like a code comment.

The reference implementation lives in `assets/template/` (one HTML fragment per page type, `[bracketed]` placeholders, shared `assets/template/style.css`) plus `assets/build.py` (assembles ordered fragments into one HTML) and `assets/export_pdf.py` (renders to A4 PDF via headless Chromium). **Always start from these, never rebuild the CSS from scratch.** First built 2026-07 for a portfolio aimed at a design-studio prospect (adventure-gear/overland accessories).

---

## The rule that matters most: attribution and anonymization

Foxio Design was founded in 2026. Almost all of Simon's actual track record — the projects worth showing — predates that, done as an employee, contractor, or freelancer for other companies. **Every portfolio built with this skill must be honest about that split, every time, without being asked.** This isn't specific to any one prospect; it's a standing constraint of Simon's career shape.

- **Intro page** must state plainly that Foxio was founded in [year] and the work shown spans the founder's prior career. Don't soften this into vague "years of experience" language — say it directly, it reads as more credible, not less.
- **Every case**, no exceptions, carries a `Role: <title> — <client or "confidential client">, <years or "freelance engagement">` line. Never phrase pre-2026 work as "Foxio designed/built/shipped X" — Foxio didn't exist yet. The person did.
- **Which cases can be named vs. must be anonymized** is a case-by-case call Simon makes (usually driven by NDA terms and by whether the client relationship is still warm). For anonymized cases: no client name, no product name, no proprietary/trademarked technology terms, and images limited to board-level photos or renders — nothing that shows the finished consumer product in a way reverse image search could identify. When in doubt about whether a case can be named, ask rather than guess; getting this wrong is a real relationship/NDA risk, not just a style nit.
- A closing line naming that further work exists under NDA (category only, e.g. "wearables, precision analog instrumentation, industrial IoT" — no specifics) is the honest way to gesture at depth without exposing anything.

## Sizing to the audience

Before writing a word, know who's reading it. A visual/industrial-design person wants photos leading each case and outcomes in plain language, jargon glossed in one clause on first use ("HDI — microvias and stacked layers to fit dense electronics in a small board"). A technical buyer (another EE, a hardware PM) can take denser spec strips and less hand-holding. Reorder or resize cases so the ones closest to the reader's own world get top billing and the most space — don't present every case with equal weight regardless of audience.

---

## Workflow

1. **Set up a project folder** for this specific deliverable (not inside this skill — this skill is the reusable template, the filled instance is a client-specific working copy, e.g. `~/Proj_/FoxioDesign/<ProjectName>/`). Structure:
   ```
   sections/          — one file per page, numeric-prefixed for order (00-cover.html, 01-intro.html, ...)
   assets/            — real images, named by case
   style.css          — copy of assets/template/style.css (or symlink)
   build.py, export_pdf.py — copies of the skill's scripts
   SPEC.md            — page-by-page plan + asset inventory, for approval before building
   README.md          — how to regenerate/reorder/swap cases
   ```
2. **Inventory the assets** the user has given you: list every image file found, and for each, state which case it maps to and why (filename keywords, or ask if ambiguous — never guess silently on an unclear file). Anything that matches no case: ask, don't drop it silently and don't guess.
3. **Write SPEC.md**: structure, per-page content plan, asset mapping table. Show it for approval before generating anything.
4. **Copy the template fragments** into `sections/`, fill in the copy per case using the content the user provided (or drafts you propose for their approval — don't invent case outcomes or numbers).
5. **Missing images**: use the `.placeholder` block from the template exactly as documented (dashed border, "IMAGE MISSING", expected filename) — never invent or generate a replacement image.
6. **Build and verify** (see below), then deliver the PDF.

Reordering later = rename the numeric prefixes in `sections/`. Swapping a case for a different audience = replace that one file's content, or drop/duplicate a compact-case block (see `case-compact-page.html`'s comment about why compact cases share one physical page and can't each be a separate file the way full-page cases are).

---

## Page catalog (from `assets/template/`)

| File | Page | Notes |
|---|---|---|
| `cover.html` | 1 | Dark page, logo + wordmark + subtitle, minimal |
| `intro.html` | 2 | Positioning paragraph, mandatory attribution statement, stat blocks |
| `case-featured.html` | 1 per case | Full page, photo fills ~55% of the page height, story + spec strip + role line + optional quote |
| `case-compact-page.html` | 1 page, several cases | Smaller cases (~60 words each) sharing one page, delimited blocks |
| `how-we-work.html` | last | Dark page, 3 engagement models, NDA line, contact block |

---

## Print verification (do this before delivering)

```bash
pip install playwright --break-system-packages -q   # once
playwright install chromium                          # once
python3 assets/build.py sections/ style.css deck.html
python3 assets/export_pdf.py deck.html deck.pdf
```

Open the PDF and check: every case's role line is present and correctly phrased (no pre-2026 work credited to "Foxio"), no anonymized case leaks a name, no placeholder was silently replaced with a guessed image, no orphaned heading, images not distorted, total page count matches the plan. Fix in the HTML/CSS source, never hand-edit the PDF.
