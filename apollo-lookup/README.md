# apollo-lookup

Check whether a list of companies figures in [Apollo.io](https://apollo.io) — by
**name**, no domain needed, no credits consumed. Built to triage [`ks-scout`](../ks-scout/)
leads, but the core lookup works for any company list.

## Scripts

| Script | What it does |
|---|---|
| `apollo_company_lookup.py` | Given company names, queries Apollo's **global B2B DB** (`organizations/search` → is it enrichable?) and **your workspace** (`accounts/search` → already prospected?). |
| `ksscout_leads_to_apollo.py` | Glue: reads a ks-scout `leads.yaml`, extracts unique `creator` names, runs them through the lookup. |

## Setup

Needs the Apollo **master key** in the environment (never hardcode it — this repo is public):

```bash
export APOLLO_API_KEY=...        # from your password manager / the foxio_apollo skill
```

Requires `pyyaml` (already available in the repo's venv, or `uv pip install pyyaml`).

## Usage

```bash
# Ad-hoc list of companies
python apollo_company_lookup.py "XFANIC" "RoboticWorx" "Edgehog Systems"

# From a file (one name per line)
python apollo_company_lookup.py --file companies.txt

# Straight from a ks-scout run
python ksscout_leads_to_apollo.py ~/Development/foxio-utilities/ks-scout/output/leads.yaml
```

## Caveats (read before trusting a hit)

- **Name search is fuzzy.** Apollo ranks by relevance and returns a top hit even for
  unrelated firms sharing a token (`Taylor` → *Taylor Root*, `ShowMo` → *ShowMojo*).
  The script filters by normalized-name containment, but **always eyeball the returned
  domain + industry** before acting.
- **Indie Kickstarter creators mostly do NOT map to Apollo's DB** — they're individuals
  or one-product brands, not the established B2B companies Apollo indexes. For ks-scout
  leads, real contact discovery usually comes from the KS project page / the creator's
  LinkedIn, not Apollo.
- Endpoint note: `mixed_companies/api_search` returns **404**; use `organizations/search`.

API details and verified endpoints live in the `foxio_apollo` skill.
