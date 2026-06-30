#!/usr/bin/env python3
"""
ksscout_leads_to_apollo.py — bridge ks-scout leads.yaml -> Apollo company lookup.

Reads a ks-scout output file (output/leads.yaml), extracts the unique `creator`
names, and runs them through apollo_company_lookup.lookup() to see which figure
in Apollo's global DB and which are already in your workspace.

Usage:
  python ksscout_leads_to_apollo.py [path/to/leads.yaml]
  (defaults to ~/Development/foxio-utilities/ks-scout/output/leads.yaml)

Requires PyYAML and apollo_company_lookup.py in the same dir (or PYTHONPATH).

NOTE / learning from the 2026-06-29 run: ks-scout leads are indie Kickstarter
creators (often individuals or one-product brands). Most do NOT map cleanly to
Apollo's B2B DB, and name matches are frequently false positives (a shared token
like "Taylor" or "Sierro" hits an unrelated firm). Apollo enrichment is a poor
fit for KS-creator leads vs. the established ID-studio ICP. Verify every hit.
"""
import sys
from pathlib import Path

import yaml
from apollo_company_lookup import lookup

DEFAULT = Path.home() / "Development/foxio-utilities/ks-scout/output/leads.yaml"


def unique_creators(leads_path: Path):
    data = yaml.safe_load(leads_path.read_text(encoding="utf-8"))
    seen, out = set(), []
    for d in data:
        c = (d.get("creator") or "").strip()
        if c and c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


def main():
    leads_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    creators = unique_creators(leads_path)
    print(f"Chequeando {len(creators)} creadores de {leads_path.name} en Apollo...\n")
    db_hits, ws_hits = lookup(creators)
    print("\n" + "=" * 80)
    print(f"En Apollo DB: {len(db_hits)}/{len(creators)} (VERIFICAR cada uno)   |   En tu workspace: {len(ws_hits)}")


if __name__ == "__main__":
    main()
