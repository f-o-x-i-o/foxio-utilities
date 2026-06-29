"""YAML I/O for nrich — read ks-scout leads, write enriched output."""

import json
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
import yaml


LEADS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "ks-scout" / "output"


def find_latest_leads(leads_dir: Path = LEADS_DIR) -> Path:
    """Auto-discover the most recent leads_YYYYMMDD.yaml in ks-scout/output/."""
    pattern = re.compile(r"^leads_(\d{8})\.yaml$")
    best: tuple[int, Path] | None = None

    if not leads_dir.exists():
        raise FileNotFoundError(f"Leads directory not found: {leads_dir}")

    for p in leads_dir.iterdir():
        m = pattern.match(p.name)
        if m:
            yyyymmdd = int(m.group(1))
            if best is None or yyyymmdd > best[0]:
                best = (yyyymmdd, p)

    if best is None:
        raise FileNotFoundError(
            f"No leads_YYYYMMDD.yaml files found in {leads_dir}"
        )

    return best[1]


def read_leads(path: str | Path) -> list[dict[str, Any]]:
    """Parse a ks-scout YAML file and validate it's a list of leads."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Leads file not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a YAML list in {path}, got {type(data).__name__}")

    if len(data) == 0:
        raise ValueError(f"Leads file {path} is an empty list")

    # Validate each lead has minimum required fields
    for i, lead in enumerate(data):
        if not isinstance(lead, dict):
            raise ValueError(f"Lead at index {i} is not a mapping (found {type(lead).__name__})")
        for field in ("name", "url"):
            if field not in lead:
                raise ValueError(f"Lead at index {i} missing required field '{field}'")

    return data


def write_enriched(leads: list[dict[str, Any]], input_path: Path) -> Path:
    """Write enriched leads as <basename>_enriched.yaml next to the input file."""
    output_path = input_path.with_name(input_path.stem + "_enriched.yaml")

    with open(output_path, "w") as f:
        yaml.dump(leads, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return output_path


def _build_json_entry(lead: dict, enriched: dict) -> dict:
    """Build a JSON entry in the linkedin_orphans.json format from enriched data."""
    contact = enriched.get("contact", {})
    company = enriched.get("creator", "") or enriched.get("name", "").split("|")[0].strip()
    now_ms = int(time.time() * 1000)

    # Derive headline from title
    headline = contact.get("title", "")
    if not headline and contact.get("name"):
        headline = f"{contact['name']}"
    if not headline:
        headline = enriched.get("name", "")

    # Determine link_type
    link_type = "personal"
    linkedin_url = contact.get("linkedin", "")
    if linkedin_url and "/company/" in linkedin_url:
        link_type = "company"

    # Determine source
    source = contact.get("source", "")
    if source and source != "linkedin":
        source = "google" if source == "web_search" else source
    elif source == "linkedin":
        source = "google"
    if not source:
        source = "google"

    return {
        "id": uuid.uuid4().hex[:13],
        "name": contact.get("name", enriched.get("creator", "")),
        "headline": headline,
        "companies": [company] if company else [],
        "company": company,
        "email": contact.get("email", ""),
        "linkedinUrl": linkedin_url,
        "addedAt": now_ms,
        "sequenceStep": 0,
        "nextActionAt": now_ms,
        "stepHistory": [],
        "coldSequenceStep": 0,
        "coldStepHistory": [],
        "messages": [],
        "status": "warming_up",
        "notes": "",
        "website": contact.get("website", enriched.get("url", "")),
        "source": source,
        "link_type": link_type,
    }


def write_json_outputs(leads: list[dict], input_path: Path) -> tuple[Path | None, Path | None]:
    """Write JSON outputs split by contact type.

    Returns (email_path, linkedin_only_path).
    """
    with_email = []
    linkedin_only = []

    for lead in leads:
        contact = lead.get("contact", {})
        entry = _build_json_entry(lead, lead)

        if contact.get("email"):
            with_email.append(entry)
        elif contact.get("linkedin"):
            linkedin_only.append(entry)

    base = input_path.stem
    email_path = None
    linkedin_path = None

    if with_email:
        email_path = input_path.with_name(f"{base}_with_email.json")
        with open(email_path, "w") as f:
            json.dump(with_email, f, indent=2)
        print(f"📧 JSON with email written to: {email_path} ({len(with_email)} contacts)")

    if linkedin_only:
        linkedin_path = input_path.with_name(f"{base}_linkedin_only.json")
        with open(linkedin_path, "w") as f:
            json.dump(linkedin_only, f, indent=2)
        print(f"🔗 JSON LinkedIn only written to: {linkedin_path} ({len(linkedin_only)} contacts)")

    return email_path, linkedin_path
