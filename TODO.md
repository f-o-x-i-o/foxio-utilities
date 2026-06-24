# TODO

## enrich script

**What:** a new script that takes the `output/leads.yaml` and turns it into
actionable outreach lists.

**Pipelines to produce:**

1. **Email sequencing** — leads with a known email address → CSV ready for
   Apollo.io / Smartlead / Instantly.
2. **LinkedIn sequencing** — leads without email but with founder/team names
   → CSV with name + company for manual LinkedIn search or HeyReach.
3. **Discard pile** — leads that are MED confidence or look like false positives
   on second review.

**Heuristics for sorting:**
- `emails` non-empty → email pipeline (even if just one address)
- `emails` empty AND `team` non-empty → LinkedIn pipeline (you have names to search)
- `emails` empty AND `team` empty AND confidence < 0.8 → discard (too thin)
- `ee_gap == "MED"` → review manually, usually discard unless the product is in a
  category where "MED = they have a manufacturer but need a real EE"

**Input:** `output/leads.yaml`
**Output:** `output/email_leads.csv`, `output/linkedin_leads.csv`,
`output/discarded.csv` (or similar, date-stamped)
