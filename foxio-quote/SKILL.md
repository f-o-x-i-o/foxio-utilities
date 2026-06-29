---
name: foxio-quote
description: Build a professional client quote (presupuesto) for Foxio Design, Simon Bourguigne's hardware/firmware consultancy. Use this whenever Simon asks to create, draft, build, or update a quote, proposal, presupuesto, or cotización for a client (Upwork prospects, direct clients, NDA-covered engagements). Produces a responsive, print-clean HTML document in the Foxio visual style that Simon exports to PDF. Trigger on any mention of quoting a client, pricing an engagement, fixed-bid vs hourly, scope-and-hours breakdown, or turning a client conversation into a formal quote, even if the word "skill" is never used. Handles both large multi-phase engagements (the full structure) and short jobs like design reviews or audits (a simple one-page quote with Standard-vs-Rush pricing).
---

# Foxio Design — Client Quote Builder

This skill builds client-facing quotes for **Foxio Design** (Simon Bourguigne, hardware & firmware consultancy, Mar del Plata, Argentina). Output is a single self-contained HTML file that looks right on phone and laptop, and exports to a clean multi-page PDF. Simon opens the HTML in his browser and prints to PDF himself.

The reference implementation lives in `assets/template.html`. It is a complete, working quote with the exact CSS, print rules, and section structure that have already been refined and approved. **Always start from the template, never rebuild the CSS from scratch.**

---

## First: how big is this engagement?

Before anything, size the document to the job. The template carries the full machinery for a **substantial, multi-phase engagement** (a board or firmware build, several phases, several thousand dollars): the open-risk section, a scope-and-hours table, fixed-vs-hourly pricing, a timeline section, a terms list. That structure earns its space when the money and the risk are large.

For a **short engagement** (a design review, an audit, a one-off fixed task, roughly a day or two of work) the same structure is overkill and actively hurts. A four-page document for a fourteen-hour review reads as bloat and undercuts the price. Match the document to the job: a short quote should be about **one page** and simple.

**Short-quote recipe** (strip the template down to):
- **Masthead** (unchanged).
- **"What's Included"**: a short `.terms` arrow-list of what the client gets, five or six lines, instead of the scope-and-hours table. Skip the per-phase hour breakdown; for a flat-priced short job the hours aren't the point.
- **Pricing**: the two cards (often Standard vs Rush, see Pricing model).
- **A single closing `.note`** that absorbs what used to be Terms: review-only / any redesign is separate, plus any scope boundary. One or two sentences, not a list. Write it to **stand on its own**: the PDF may be read without the cover message, so a scope boundary like "this quote covers the left board" must first establish the context ("there are two boards, left and right"). Don't lean on the chat thread to make the note make sense.
- **Footer** (unchanged).
- **Delete** the Open-Engineering-Risk section, the Scope-&-Hours table, and the standalone Timeline section.

To land it on one page, append a small `@media print{}` block at the end of `<style>` that tightens the vertical rhythm (smaller `h1`, ~9px `section` padding, ~5px `.terms li` padding, smaller `.price-card` padding and `.big`, small `.foot` margin). Render, read the PDF, confirm it is genuinely one page. A common failure is the footer alone slipping to page 2; if that happens, shave a little more. This compression lives on the working copy only, it never touches the template.

---

## Workflow

1. **Gather the inputs** (see "What you need" below). If a client conversation is in context (e.g. an Upwork thread), mine it for the technical scope, the client name, the open risks, and anything already agreed. Don't re-ask for things that are already on the table.
2. **Read `assets/template.html`** to load the structure and style.
3. **Compute the numbers** with the pricing model below. Show the arithmetic so Simon can sanity-check.
4. **Fill the template**: replace the `{{PLACEHOLDERS}}` and rewrite each section's body for this specific engagement.
5. **Verify print output**: render to PDF (see "Print verification") and check page breaks before delivering.
6. **Deliver** to the output folder and present it. Locally (Simon's Mac) that is `~/Desktop/foxio-quote-<client>/`, where you generate the clean PDF straight from headless Chrome (see Print verification). In the Claude.ai sandbox it is `/mnt/user-data/outputs/` and Simon prints to PDF himself (remind him to disable "Headers and footers").

---

## What you need (ask only for what's missing)

- **Client name + company** (e.g. "Phillip Shatkin · INTRCPT LLC")
- **Project name** (short, e.g. "Precision Analog Front-End Rebuild")
- **One-line subtitle** describing the work
- **Confidentiality line** if under NDA (e.g. "Under INTRCPT LLC NDA · v2"), else a neutral line
- **The phases and estimated hours** — Simon usually provides these as a ball-park list. If he doesn't, propose a breakdown from the standard phase set below and let him correct it.
- **Rate** (default $70/h unless Simon says otherwise)
- **Any open risks / R&D recommendations** that should be flagged
- **Availability constraints** (trips, etc.) for the timeline
- **Ref code** (Simon's convention: `FX-<CLIENT>-NNN`)

---

## Pricing model (Simon's method)

Two options are **always presented in the same document**. Fixed bid is the default/recommended; hourly is the alternative. Simon's site promises exactly this ("We quote both fixed-price and hourly in the same document, you pick what fits").

**Fixed bid** = `1.3 × rate × total_hours`
- The `1.3` is a **30% uncertainty margin**. It is what lets Simon commit to one number and absorb the risk so the client never gets open-ended invoices.
- Round to the nearest dollar. Show the formula explicitly: `1.3 × $70/h × 121 h = $11,011`.

**Hourly** = `rate × total_hours` (no margin)
- Present as "billed against actual hours, no uncertainty margin, may land under or over the fixed bid."
- Show the on-estimate figure: `~121 h est. = ~$8,470 if on-estimate`.

**Worked example (do the math in your head/code, never copy these numbers):**
- 121 h at $70/h → fixed `1.3 × 70 × 121 = 11,011`; hourly on-estimate `70 × 121 = 8,470`.

Always recompute from scratch for the actual hours. Never reuse a prior quote's numbers.

**Alternative axis, Standard vs Rush (for short / turnaround-driven jobs):** fixed-vs-hourly answers "how do you want to be billed," which is the real question on a big engagement. On a short review the client's actual question is usually *speed*, not billing model. There, make the two cards **Standard** (recommended) and **Rush**: Rush is a flat multiple (e.g. 2×) that prices jumping the queue and bumping committed work. Both cards are flat-priced and same-scope; they differ only in schedule. Don't force the fixed/hourly split onto a job where turnaround is the decision.

---

## Standard phase set

Typical phases for a PCB/firmware engagement, in a sensible execution order. Adjust per project; not every phase applies every time.

- **Onboarding** — study the system, build technical clarity
- **BOM reconstruction** — build the working BOM (esp. when rebuilding from PDFs)
- **Component library** — symbols + footprints from scratch when no native files exist
- **Schematic design** — full rebuild + any protection topology
- **PCB design** — multilayer layout, the biggest line item usually
- **Release** — manufacturing package (Gerbers, NC drill, BOM, native files, assembly docs)
- **Review cycle (1×)** — one iteration included; further changes billed hourly
- **Firmware block diagram** — architecture documentation only (sensor init, sampling, packaging), NOT implementation, unless separately scoped

Order phases logically for the project. A special R&D/de-risk item that carries extra uncertainty (e.g. an unproven analog channel) can be flagged in its own row and described as such, and/or proposed as a **separate, separately-quoted R&D phase** that runs ahead of the main design (see "Open risk" below).

---

## Document structure

The template has these sections in order. Keep this skeleton; rewrite the prose per engagement. (That is for a full engagement. For a short review or audit, collapse it to masthead + What's Included + Pricing + a closing note + footer, see "First: how big is this engagement?" above.)

1. **Masthead** — logo, "QUOTE." as the big title, project name as the line under it, subtitle, and a meta row (For / From / Date / Ref). The opening title must clearly read as a **quote**, not as a project name.
2. **Open Engineering Risk** (when there is one) — name the risk honestly, state Simon's approach, give a "Risk" callout and a "My Recommendation" callout. See rules below.
3. **Scope & Hours** — the phase table with hours and a total. A note states base vs. total.
4. **Pricing** — the two option cards (fixed bid recommended, hourly alternative).
5. **Timeline** — effort-to-weeks, availability caveats, no hard dates unless a start is agreed.
6. **Terms & Assumptions** — the fine print, as a list.
7. **Footer** — contact + signature.

---

## Voice & writing rules (DO / DON'T)

These were refined directly with Simon. They are not optional.

**DON'T:**
- **Never use the em-dash character (`—`).** Forbidden. Use commas, colons, periods, or "to" for ranges. Check the final file: it must contain zero `—`.
- **No blog-post / hype headers.** Section titles are plain nouns: "Pricing", "Timeline", "Terms & Assumptions", "Scope & Hours". Not "Two Ways To Buy. You Pick." or "Six To Eight Weeks Of Work. One Honest Caveat."
- **No WhatsApp/chat register.** Write professionally. "I'm away July 21" → "I have one week of scheduled unavailability from July 21 to 28."
- **No noise that obscures the document.** Cut sentences that explain the obvious or editorialize the pricing ("the basis I'm betting the fixed price on" type filler). Convey the message, reduce noise.
- **Don't invent agreed facts.** Kickoff dates, start dates, and delivery dates are a separate conversation unless Simon says they're agreed. Don't present an example date as if it's settled. *Exception:* a short review that starts within days can carry concrete `start → delivery` dates right in the pricing cards. The no-dates rule protects large engagements whose schedule genuinely hinges on an unset kickoff; a two-day review has no such problem. Keep the dates realistic and say you'll confirm them on acceptance.
- **Don't present an optional recommendation as a given.** If Simon recommends an R&D phase, it is his professional recommendation; the client may decline and go straight to the design. Always state the client can proceed directly.
- **Don't flag vendor/chipset preferences as gaps**, and don't over-explain pricing.
- **Don't name other clients** without confirmed permission.

**DO:**
- Direct, senior, non-apologetic tone. Plain verbs, sentence-level clarity.
- State assumptions explicitly in Terms so the number isn't padded with hidden guesses.
- Frame scope honestly: what's included, what's one review, what's billed hourly.
- When there's a real engineering risk, surface it. It's what differentiates Simon from whoever quoted before. Be specific and technical, but don't manufacture drama.
- Keep firmware block-diagram scope tight: only what's needed to instrument and operate the measurement.
- Keep it reasonably concise.

---

## Open-risk / R&D-phase rules

When a block is architecturally unresolved (not just incomplete):
- Name it in an **Open Engineering Risk** section.
- State Simon's intended approach in one short paragraph.
- "Risk" callout (amber): what the genuine uncertainty is, and why it can't be settled from the schematic/spec alone.
- "My Recommendation" callout: Simon **recommends** a short, separately-quoted R&D phase that builds only the minimum to prove viability at the bench, **but it isn't mandatory** and the client may proceed directly to the design and carry the risk into the work.
- The R&D phase, if taken, is **not included in the quote below and is quoted separately**, and it runs ahead of the main work (shifting the start).
- In Terms, the corresponding line says the risk is "best settled in the recommended R&D phase before layout commit, but you may proceed directly."

---

## Visual style (already in the template, don't reinvent)

Light theme (the dark site translated to paper). Key tokens:
- Background `#f4f2ec`, paper `#ffffff`, ink `#16181d`, accent (Foxio orange) `#e0532f`.
- Display face: **Archivo Narrow**, uppercase, tight, for the big "QUOTE." and all H2s.
- Body: **Archivo**. Data/labels/eyebrows/formulas: **JetBrains Mono**.
- Eyebrows are mono, uppercase, prefixed with `//` (e.g. `// PRICING`).
- The accent is spent sparingly: the "." after QUOTE, eyebrows, the recommended card border, risk callout accents.
- Callout variants: default (orange left border), `.warn` (amber, for Risk), `.ok` (green, rarely used).
- Pricing: two cards side by side; the recommended one has a heavier border and a "RECOMMENDED" pill.

The template's CSS and `@media print` block are tuned. **Do not regenerate them.** If you must adjust, edit minimally and re-verify print.

---

## The logo

The masthead uses Foxio's badge logo, referenced by URL:
`https://foxiodesign.com/assets/logo-badge.png`

- **Default (URL reference):** works fine when Simon opens the HTML in his own browser, because his machine can reach foxiodesign.com. This is what the template ships with.
- **Robust (base64-embedded):** for a PDF that must render the logo even offline or when external assets are blocked, embed the PNG inline as a data URI. If Simon uploads `logo-badge.png` (or it's available on disk), convert it: `base64 -w0 logo-badge.png`, then set `src="data:image/png;base64,...."`. The sandbox cannot download from foxiodesign.com, so embedding requires Simon to provide the file.

If the logo renders broken in a sandbox PDF preview, that's expected (no network to foxiodesign.com); it is NOT a layout bug. Note it to Simon and offer the base64 path.

---

## Print verification (do this before delivering)

The whole point is a clean PDF. The template's print rules already: stop the masthead from taking a page alone, compress section padding, keep cards/callouts/table-rows/list-items from splitting across pages, glue headings to their content, and keep the total-hours line on one line.

Render and eyeball the page breaks:

```bash
pip install playwright pdf2image --break-system-packages -q
playwright install chromium
python3 - << 'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto('file:///home/claude/quote.html', wait_until='networkidle', timeout=10000)
    pg.pdf(path='preview.pdf', format='A4', print_background=True,
           margin={'top':'14mm','bottom':'14mm','left':'0','right':'0'})
    b.close()
from pdf2image import convert_from_path
imgs = convert_from_path('preview.pdf', dpi=80)
print('pages:', len(imgs))
for i,im in enumerate(imgs): im.save(f'pg{i+1}.png')
PY
```

Then `view` each `pgN.png` and confirm: no near-empty pages, no heading orphaned from its table/cards, no block split mid-way. A well-formed quote of this size lands around 5 pages. The logo will show broken in-sandbox; ignore that.

**Running locally on Simon's Mac (not the Claude.ai sandbox):** the sandbox paths above don't apply. Output to a per-client folder, `~/Desktop/foxio-quote-<client>/` (HTML, PDF, and the chat/cover message together), and generate the PDF straight from headless Chrome. This skips the manual print step and the header/footer problem in one shot, because a programmatic print-to-pdf has no headers or footers:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --no-pdf-header-footer --virtual-time-budget=10000 \
  --print-to-pdf="$OUT/quote.pdf" "file://$OUT/quote.html"
```

The logo loads fine here (the local machine reaches foxiodesign.com), so no base64 is needed. Verify by **reading the generated PDF directly** (the Read tool renders PDF pages) and checking the page count and breaks, which replaces the playwright/pdf2image step above.

**Browser header/footer:** the date and `file:///...` path that appear on each printed page come from Chrome's print dialog, not the CSS. This only applies when Simon prints to PDF himself (the sandbox flow); always remind him to turn off "Headers and footers" then. The headless-Chrome route above has none, so nothing to disable.

---

## Filling the template

`assets/template.html` is **fully generic**: the CSS and print rules are final, and the body is a neutral skeleton of placeholders with HTML comments explaining each section. There is no client data in it. Replace every `{{PLACEHOLDER}}` and follow the comments.

**Masthead placeholders:**
- `{{CLIENT}}` — "Name · Company"
- `{{PROJECT_NAME}}` — short project name (renders uppercase under QUOTE)
- `{{PROJECT_SUBTITLE}}` — one-line description
- `{{CONFIDENTIALITY_LINE}}` — NDA line or neutral
- `{{DATE}}` — e.g. "Jun 12, 2026"
- `{{REF}}` — e.g. "FX-INTRCPT-001"

**Open risk (optional section):** `{{RISK_TITLE}}`, `{{RISK_LEAD}}`, `{{RISK_APPROACH}}`, `{{RISK_BODY}}`, `{{RD_PHASE_DESCRIPTION}}`. **Delete the entire `<section>` if there is no open risk**, and also delete the R&D note in Pricing.

**Scope table:** `{{SCOPE_LEAD}}`, then one row per phase (`{{PHASE_N_NAME}}`, `{{PHASE_N_DESC}}`, `{{PHASE_N_HOURS}}`). The template ships with 3 placeholder rows; **duplicate or delete `<tr>` blocks** to match the real phase count. Add `class="ec"` to any high-uncertainty row to highlight it. `{{TOTAL_HOURS}}` and `{{SCOPE_NOTE}}` close it out.

**Pricing:** `{{FIXED_PRICE}}`, `{{FIXED_SUB}}`, `{{RATE}}`, `{{HOURLY_TOTAL}}`. The formula line uses `{{RATE}}` and `{{TOTAL_HOURS}}`.

**Timeline:** `{{TIMELINE_LEAD}}`, `{{TIMELINE_DETAIL}}`, `{{TIMELINE_NET}}`.

**Terms:** `{{TERM_1..3}}` plus the two fixed terms (review cycle, delivery) already written. Add or remove `<li>` items to match the real assumptions.

The footer (contact + signature) is fixed Foxio info; leave it as-is.

When you fill it, copy `assets/template.html` to a working path (e.g. `/home/claude/quote.html`) first, then edit the copy. Never edit the skill's template in place.

---

## Final checklist before delivery

- [ ] Numbers recomputed from scratch; both options present (fixed + hourly, or Standard + Rush for a short job).
- [ ] Zero `—` characters in the file.
- [ ] Section headers are plain nouns, no hype.
- [ ] R&D/optional items framed as recommendation with a "proceed directly" option.
- [ ] Dates handled right: weeks-of-effort for a large job, or concrete start → delivery for a short review.
- [ ] Terms list the real assumptions.
- [ ] Print preview rendered and page breaks checked.
- [ ] File saved to the output folder (local `~/Desktop/foxio-quote-<client>/` or sandbox `/mnt/user-data/outputs/`) and presented; for a short quote, confirmed it is genuinely one page.
- [ ] Reminded Simon to disable browser headers/footers, and offered base64 logo if needed.
