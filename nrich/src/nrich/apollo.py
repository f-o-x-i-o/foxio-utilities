"""Apollo.io integration for nrich — search decision makers and get verified emails."""

import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from nrich.config import Config

BASE = "https://api.apollo.io/api/v1"

SENIORITY_ORDER = [
    "owner", "founder", "c_suite", "partner", "vp", "head", "director",
]


@dataclass
class ApolloResult:
    """Result from the Apollo enrichment stage."""
    email: str | None = None
    email_status: str | None = None
    name: str | None = None
    title: str | None = None
    source: str = "apollo"
    confidence: str | None = None


class ApolloClient:
    """Client for Apollo.io People Search and Enrichment APIs."""

    def __init__(self, config: Config, client: httpx.Client | None = None):
        self.config = config
        self.client = client or httpx.Client(
            headers={
                "x-api-key": config.apollo_api_key,
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )
        self._call_times: list[float] = []
        self._min_interval = 3600.0 / config.apollo_rate_limit  # seconds between calls

    def _rate_limit_wait(self) -> None:
        """Enforce Apollo rate limit by sleeping if needed."""
        now = time.monotonic()
        # Remove timestamps older than 1 hour
        self._call_times = [t for t in self._call_times if now - t < 3600]
        if len(self._call_times) >= self.config.apollo_rate_limit:
            oldest = self._call_times[0]
            wait = 3600 - (now - oldest)
            if wait > 0:
                time.sleep(wait)
        self._call_times.append(time.monotonic())

    def _respect_min_delay(self) -> None:
        """Ensure minimum delay between API calls."""
        if self._call_times:
            elapsed = time.monotonic() - self._call_times[-1]
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)

    def _call(self, method: str, path: str, json_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an API call with rate limiting and retry."""
        self._rate_limit_wait()
        self._respect_min_delay()

        url = f"{BASE}{path}"
        for attempt in range(3):
            try:
                if method == "POST":
                    r = self.client.post(url, json=json_data)
                else:
                    r = self.client.get(url, params=json_data)

                if r.status_code == 429:
                    time.sleep(60)
                    continue
                if r.status_code == 401:
                    raise RuntimeError("Apollo API: invalid API key (401)")
                if r.status_code == 403:
                    raise RuntimeError("Apollo API: not a master key (403) — sequence endpoints require master key")
                r.raise_for_status()
                return r.json()
            except httpx.TimeoutException:
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise RuntimeError(f"Apollo API: timeout after 3 retries ({path})")
            except httpx.ConnectError:
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise RuntimeError(f"Apollo API: connection failed after 3 retries ({path})")

        raise RuntimeError("Apollo API: rate limited after 3 retries (429)")

    def search_people(self, domain: str) -> list[dict[str, Any]]:
        """Search for decision makers at a domain via Apollo People Search."""
        data = self._call("POST", "/mixed_people/api_search", {
            "q_organization_domains_list": [domain],
            "person_seniorities": SENIORITY_ORDER,
            "per_page": 10,
            "page": 1,
        })
        return data.get("people", [])

    def enrich_person(self, person_id: str) -> tuple[str | None, str | None]:
        """Enrich a person by Apollo ID to get email and status."""
        data = self._call("POST", "/people/match", {
            "id": person_id,
            "reveal_personal_emails": False,
        })
        person = data.get("person", {})
        return person.get("email"), person.get("email_status")

    def extract_domain(self, url: str) -> str | None:
        """Extract a clean domain from a project URL for Apollo search."""
        import re
        m = re.search(r"https?://(?:www\.)?([^/]+)", url)
        if m:
            return m.group(1)
        return None

    def search_contacts(self, domain: str) -> list[dict[str, Any]]:
        """Search existing Apollo contacts by organization domain."""
        data = self._call("POST", "/contacts/search", {
            "q_organization_domains": [domain],
            "per_page": 10,
            "page": 1,
        })
        return data.get("contacts", [])

    def run_apollo_stage(self, domain: str) -> ApolloResult:
        """Full Apollo pipeline for one domain: search → enrich → return verified email."""
        people = self.search_people(domain)
        if not people:
            return ApolloResult()

        # Sort by seniority priority (lower index = higher priority)
        def seniority_rank(p: dict[str, Any]) -> int:
            title = (p.get("title") or "").lower()
            for rank, seniority in enumerate(SENIORITY_ORDER):
                if seniority in title:
                    return rank
            return len(SENIORITY_ORDER)

        people.sort(key=seniority_rank)

        for person in people:
            if not person.get("has_email"):
                continue
            person_id = person.get("id")
            if not person_id:
                continue

            email, status = self.enrich_person(person_id)
            if email and status == "verified":
                first = person.get("first_name", "")
                last = person.get("last_name", "")
                return ApolloResult(
                    email=email,
                    email_status=status,
                    name=f"{first} {last}".strip(),
                    title=person.get("title"),
                    confidence="high",
                )

        return ApolloResult()
