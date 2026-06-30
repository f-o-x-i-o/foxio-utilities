#!/usr/bin/env python3
"""
apollo_company_lookup.py — check whether a list of companies figures in Apollo.

Two independent checks per company NAME (no domain needed, no credits consumed):
  1) organizations/search  -> Apollo's GLOBAL B2B DB. "Is this company enrichable?"
  2) accounts/search       -> YOUR workspace accounts. "Did we already prospect it?" (dedup)

VERIFIED ENDPOINTS (2026-06-29)
  - POST /api/v1/organizations/search  {"q_organization_name": NAME, "per_page": N}  -> {"organizations":[...], "pagination":{...}}
  - POST /api/v1/accounts/search       {"q_organization_name": NAME, "per_page": N}  -> {"accounts":[...], "pagination":{...}}
  - POST /api/v1/mixed_people/api_search {"q_organization_name": NAME}                -> people in Apollo DB filtered by org name
  GOTCHA: POST /api/v1/mixed_companies/api_search returns 404 on this plan. Use organizations/search instead.

CAVEAT — name matching is FUZZY. organizations/search ranks by relevance and will return a
top hit even for unrelated firms that merely share a token (e.g. "Taylor" -> "Taylor Root",
"ShowMo" -> "ShowMojo"). The norm-containment match below is a coarse filter; ALWAYS eyeball
the returned domain/industry before trusting a hit. Best signal is when name + industry + domain
all line up with the real company.

Usage:
  APOLLO_API_KEY=... python apollo_company_lookup.py "Edgehog Systems" "XFANIC" "RoboticWorx"
  python apollo_company_lookup.py --file companies.txt          # one company name per line
"""
import os, sys, json, time, re, argparse, urllib.request, urllib.error

BASE = "https://api.apollo.io/api/v1"
# Apollo master key — read from env ONLY. Never hardcode it: this repo is public.
# Get the key from the foxio_apollo skill / your password manager and export it:
#   export APOLLO_API_KEY=...
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")
if not APOLLO_API_KEY:
    sys.exit("Error: set APOLLO_API_KEY env var (Apollo master key) before running.")
H = {"x-api-key": APOLLO_API_KEY, "Content-Type": "application/json", "Cache-Control": "no-cache"}


def post(path: str, body: dict, timeout: int = 15):
    req = urllib.request.Request(f"{BASE}/{path}", data=json.dumps(body).encode(), headers=H, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:           # 401 invalid key / 403 not master / 422 validation / 429 rate
        return e.code, {"_err": e.read().decode()[:160]}
    except Exception as e:
        return "ERR", {"_err": str(e)[:160]}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _matches(a: str, b: str) -> bool:
    na, nb = _norm(a), _norm(b)
    return bool(na) and bool(nb) and (na in nb or nb in na)


def org_search_db(name: str):
    """Apollo global B2B DB. Returns the first name-matching org dict, or None."""
    code, r = post("organizations/search", {"q_organization_name": name, "per_page": 3})
    orgs = r.get("organizations", []) if isinstance(r, dict) else []
    return next((o for o in orgs if _matches(name, o.get("name", ""))), None)


def account_search_workspace(name: str):
    """Your Apollo workspace accounts (dedup). Returns first name-matching account dict, or None."""
    code, r = post("accounts/search", {"q_organization_name": name, "per_page": 3})
    accs = r.get("accounts", []) if isinstance(r, dict) else []
    return next((a for a in accs if _matches(name, a.get("name", ""))), None)


def lookup(names, sleep: float = 0.2):
    db_hits, ws_hits = [], []
    for i, name in enumerate(names, 1):
        org = org_search_db(name)
        acc = account_search_workspace(name)
        if org:
            dom = org.get("primary_domain") or org.get("website_url") or "-"
            emp = org.get("estimated_num_employees") or "?"
            ind = org.get("industry") or "-"
            db_hits.append((name, org.get("name"), dom, emp, ind))
            tag = f"DB✓ {org.get('name','')[:28]} | {str(dom)[:30]} | emp:{emp} | {ind}"
        else:
            tag = "DB— (no figura)"
        ws = "  ⭐WORKSPACE" if acc else ""
        if acc:
            ws_hits.append((name, acc.get("name")))
        print(f"[{i:>2}/{len(names)}] {name:26} -> {tag}{ws}", flush=True)
        time.sleep(sleep)
    return db_hits, ws_hits


def main():
    ap = argparse.ArgumentParser(description="Check if companies figure in Apollo (global DB + your workspace).")
    ap.add_argument("names", nargs="*", help="company names")
    ap.add_argument("--file", help="file with one company name per line")
    args = ap.parse_args()
    names = list(args.names)
    if args.file:
        names += [ln.strip() for ln in open(args.file, encoding="utf-8") if ln.strip()]
    if not names:
        ap.error("pass company names or --file")

    db_hits, ws_hits = lookup(names)
    print("\n" + "=" * 80)
    print(f"EN LA DB GLOBAL DE APOLLO (enriquecibles, VERIFICAR dominio/industria): {len(db_hits)}/{len(names)}")
    for name, oname, dom, emp, ind in db_hits:
        print(f"  • {name}  ==  {oname}  ({dom}, {emp} emp, {ind})")
    print(f"\nYA EN TU WORKSPACE APOLLO (no re-prospectar): {len(ws_hits)}")
    for name, oname in ws_hits:
        print(f"  • {name}  ==  {oname}")
    if not ws_hits:
        print("  (ninguna)")


if __name__ == "__main__":
    main()
