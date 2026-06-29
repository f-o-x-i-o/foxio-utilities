"""nrich — enrichment pipeline orchestrator."""

import re
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field

from nrich.config import load_config, Config
from nrich.io import find_latest_leads, read_leads, write_enriched, write_json_outputs
from nrich.apollo import ApolloClient, ApolloResult
from nrich.search import WebSearch, SearchResult
from nrich.report import EnrichmentStats, print_report


@dataclass
class EnrichedLead:
    """A lead enriched with contact information."""
    original: dict
    contact_email: str | None = None
    contact_linkedin: str | None = None
    contact_name: str | None = None
    contact_title: str | None = None
    source: str | None = None
    confidence: str | None = None
    discarded: bool = False


def extract_domain(url: str) -> str | None:
    """Extract domain from a URL for web searches."""
    import re
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if m:
        return m.group(1)
    return None


def domain_matches_company(email: str, company_name: str) -> bool:
    """Check if an email's domain plausibly belongs to the company."""
    email_domain = email.split("@")[-1].lower()
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower().strip())
    email_slug = re.sub(r"[^a-z0-9]", "", email_domain.split(".")[0])
    if slug and (slug in email_slug or email_slug in slug):
        return True
    return False


def extract_company(lead: dict) -> str:
    """Extract company name from a lead (prefer creator field)."""
    return lead.get("creator", "") or lead.get("name", "").split("|")[0].strip()


def enrich_lead(lead: dict, apollo: ApolloClient, web: WebSearch) -> EnrichedLead:
    """Run the 3-stage enrichment pipeline for a single lead."""
    result = EnrichedLead(original=lead)

    url = lead.get("url", "")
    company = extract_company(lead)
    creator_name = lead.get("creator", "")

    # Stage 0: Discover real company domain
    domain = web.discover_domain(company) if company else None
    if not domain and creator_name:
        domain = web.discover_domain(creator_name)

    # Stage 1: Apollo — only on a real domain, never from URL fallback
    if domain:
        apollo_result = apollo.run_apollo_stage(domain)
        if apollo_result.email and domain_matches_company(apollo_result.email, company):
            result.contact_email = apollo_result.email
            result.contact_name = apollo_result.name
            result.contact_title = apollo_result.title
            result.source = "apollo"
            result.confidence = apollo_result.confidence or "high"
            return result

    # Stage 2: LinkedIn (web search)
    if creator_name and company:
        linkedin_result = web.run_linkedin_stage(creator_name, company)
        if linkedin_result.linkedin:
            result.contact_linkedin = linkedin_result.linkedin
            result.contact_name = creator_name
            result.source = "linkedin"
            result.confidence = "medium"
            # Do NOT return — continue to web search for email

    # Stage 3: Web search email fallback
    if creator_name and company and domain:
        email_result = web.run_email_stage(creator_name, company, domain)
        if email_result.email:
            result.contact_email = email_result.email
            result.contact_name = creator_name
            if not result.source:
                result.source = "web_search"
                result.confidence = "low"
            # If we already had linkedin, keep both
            return result

    # If we got linkedin but no email, keep it
    if result.contact_linkedin:
        return result

    # No contact found at all
    result.discarded = True
    return result


def build_output_lead(enriched: EnrichedLead) -> dict | None:
    """Build the output YAML entry from an enriched lead."""
    if enriched.discarded:
        return None

    lead = dict(enriched.original)
    contact = {}

    if enriched.contact_email:
        contact["email"] = enriched.contact_email
    if enriched.contact_linkedin:
        contact["linkedin"] = enriched.contact_linkedin
    if enriched.contact_name:
        contact["name"] = enriched.contact_name
    if enriched.contact_title:
        contact["title"] = enriched.contact_title
    if enriched.source:
        contact["source"] = enriched.source
    if enriched.confidence:
        contact["confidence"] = enriched.confidence

    lead["contact"] = contact
    return lead


def run_pipeline(input_path: Path | None = None) -> int:
    """Run the full enrichment pipeline."""
    config = load_config()

    if input_path:
        input_path = Path(input_path)
    else:
        input_path = find_latest_leads()

    print(f"📂 Reading leads from: {input_path}")
    leads = read_leads(input_path)
    print(f"📊 {len(leads)} leads loaded\n")

    apollo = ApolloClient(config)
    web = WebSearch(config)
    stats = EnrichmentStats(total=len(leads))

    enriched_leads: list[dict] = []

    for i, lead in enumerate(leads):
        company = extract_company(lead)
        print(f"  [{i+1}/{len(leads)}] {company[:50]}...", end=" ", flush=True)

        result = enrich_lead(lead, apollo, web)

        if result.discarded:
            stats.discarded += 1
            print("❌ discarded")
        else:
            output = build_output_lead(result)
            if output:
                enriched_leads.append(output)
                if result.source == "apollo":
                    stats.apollo += 1
                    print(f"✅ Apollo ({result.contact_email})")
                elif result.source == "linkedin":
                    stats.linkedin += 1
                    print(f"🔗 LinkedIn ({result.contact_linkedin})")
                else:
                    stats.web_search += 1
                    print(f"🌐 Web search ({result.contact_email})")

    if enriched_leads:
        output_path = write_enriched(enriched_leads, input_path)
        print(f"\n📝 Output written to: {output_path}")
        write_json_outputs(enriched_leads, input_path)
    else:
        print("\n⚠ No leads were enriched — no output file written.")

    print_report(stats)

    return 0 if stats.enriched > 0 else 1
