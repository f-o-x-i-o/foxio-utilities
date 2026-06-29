"""Web search for nrich — DuckDuckGo (via ddgs) + optional Google CSE."""

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from ddgs import DDGS

from nrich.config import Config

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


@dataclass
class SearchResult:
    """Result from a web search stage."""
    email: str | None = None
    linkedin: str | None = None
    source: str | None = None
    confidence: str | None = None


SKIP_DOMAINS = {
    "kickstarter.com", "facebook.com", "twitter.com", "instagram.com",
    "linkedin.com", "youtube.com", "reddit.com", "github.com",
    "wikipedia.org", "amazon.com", "crowdfundinsider.com",
    "indiegogo.com", "producthunt.com", "techcrunch.com",
    "google.com", "bing.com", "ycombinator.com",
}


class WebSearch:
    """Web search via DuckDuckGo (no API key) + optional Google CSE."""

    def __init__(self, config: Config, client: httpx.Client | None = None):
        self.config = config
        self.client = client or httpx.Client(timeout=config.timeout)

    def search(self, query: str, num: int = 5) -> list[dict[str, str]]:
        """Run a web search. Returns list of {title, link, snippet} dicts."""
        results = self._ddg_search(query, num)
        if not results and self._google_available():
            results = self._google_search(query, num)
        return results

    def _google_available(self) -> bool:
        return bool(self.config.google_api_key and self.config.google_cx)

    def _ddg_search(self, query: str, num: int = 5) -> list[dict[str, str]]:
        """Search via duckduckgo-search library — handles rate limits and bot detection."""
        try:
            with DDGS() as ddgs:
                results = []
                for i, r in enumerate(ddgs.text(query, max_results=num)):
                    if i >= num:
                        break
                    results.append({
                        "title": r.get("title", ""),
                        "link": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
                return results
        except Exception:
            return []

    def _google_search(self, query: str, num: int = 5) -> list[dict[str, str]]:
        """Google Custom Search."""
        params = {
            "key": self.config.google_api_key,
            "cx": self.config.google_cx,
            "q": query,
            "num": min(num, 10),
        }
        try:
            r = self.client.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
            )
            r.raise_for_status()
            data = r.json()
            items = data.get("items", [])
            return [
                {"title": item.get("title", ""),
                 "link": item.get("link", ""),
                 "snippet": item.get("snippet", "")}
                for item in items
            ]
        except Exception:
            return []

    def search_linkedin(self, person_name: str, company: str) -> str | None:
        """Search for a LinkedIn profile URL for a person at a company."""
        query = f'"{person_name}" "{company}" LinkedIn'
        results = self.search(query)
        for r in results:
            link = r.get("link", "")
            if "linkedin.com/in/" in link:
                m = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[^/?\s]+)", link)
                if m:
                    return m.group(1)
            snippet = r.get("snippet", "")
            url_match = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[^/?\s]+)", snippet)
            if url_match:
                return url_match.group(1)
        return None

    def discover_domain(self, company_name: str) -> str | None:
        """Discover the real company domain — first guess common patterns, then web search."""
        guess = self._guess_domain(company_name)
        if guess:
            return guess
        return self._search_domain(company_name)

    def _guess_domain(self, company_name: str) -> str | None:
        """Try common domain patterns (company.com, getcompany.com, etc.) via HEAD."""
        slug = re.sub(r"[^a-z0-9]+", "", company_name.lower().strip()).strip()
        if not slug or len(slug) < 3:
            return None
        for suffix in ("llc", "inc", "ltd", "gmbh", "co", "corp", "limited"):
            if slug.endswith(suffix) and len(slug) > len(suffix) + 2:
                slug = slug[:-len(suffix)]
                break

        patterns = [f"{slug}.com", f"{slug}.io", f"{slug}.org", f"get{slug}.com"]

        for hostname in patterns:
            for scheme in ("https://", "http://"):
                try:
                    r = self.client.head(
                        f"{scheme}{hostname}",
                        follow_redirects=True,
                        timeout=5,
                    )
                    if r.status_code < 500:
                        parsed = urlparse(str(r.url))
                        domain = parsed.netloc.lower()
                        if domain.startswith("www."):
                            domain = domain[4:]
                        if domain not in SKIP_DOMAINS:
                            return domain
                except Exception:
                    pass
        return None

    def _search_domain(self, company_name: str) -> str | None:
        """Search the web for the company's domain."""
        queries = [
            f'"{company_name}" official website',
            f'"{company_name}" company',
        ]
        for query in queries:
            results = self.search(query)
            for r in results:
                link = r.get("link", "")
                if not link:
                    continue
                parsed = urlparse(link)
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
                if not domain or domain.count(".") < 1:
                    continue
                if domain in SKIP_DOMAINS:
                    continue
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", domain):
                    continue
                if len(domain) > 50:
                    continue
                return domain
        return None

    def search_email(self, person_name: str, company: str, domain: str) -> str | None:
        """Search for an email for a person at a company, filtered by domain."""
        queries = [
            f'"{person_name}" "{company}" email contact',
            f'"{person_name}" @{domain}',
            f'"{company}" contact email',
        ]
        seen = set()
        for query in queries:
            results = self.search(query)
            for r in results:
                snippet = r.get("snippet", "")
                link = r.get("link", "")
                text = f"{snippet} {link}"
                emails = EMAIL_PATTERN.findall(text)
                for email in emails:
                    if email.lower() in seen:
                        continue
                    seen.add(email.lower())
                    email_domain = email.split("@")[-1].lower()
                    if domain and (domain in email_domain or email_domain in domain):
                        return email
            # Fetch page content for deeper email extraction
            for r in results:
                link = r.get("link", "")
                if not link:
                    continue
                try:
                    resp = self.client.get(link, timeout=10)
                    emails = EMAIL_PATTERN.findall(resp.text)
                    for email in emails:
                        if email.lower() in seen:
                            continue
                        seen.add(email.lower())
                        email_domain = email.split("@")[-1].lower()
                        if domain and (domain in email_domain or email_domain in domain):
                            return email
                except Exception:
                    continue
        return None

    def run_linkedin_stage(self, person_name: str, company: str) -> SearchResult:
        """LinkedIn search stage."""
        linkedin = self.search_linkedin(person_name, company)
        if linkedin:
            return SearchResult(
                linkedin=linkedin,
                source="linkedin",
                confidence="medium",
            )
        return SearchResult()

    def run_email_stage(self, person_name: str, company: str, domain: str) -> SearchResult:
        """Web search email fallback stage."""
        email = self.search_email(person_name, company, domain)
        if email:
            return SearchResult(
                email=email,
                source="web_search",
                confidence="low",
            )
        return SearchResult()
