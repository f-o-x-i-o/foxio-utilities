from __future__ import annotations
import html as html_module
import re
from .cache import Cache
from .config import Config
from .http_client import RateLimitedClient

_GQL = """
{{
  project(pid: {pid}) {{
    name
    description
    story
    risks
    url
    projectShortLink
    percentFunded
    backersCount
    deadlineAt
    launchedAt
    creator {{
      name
      biography
      launchedProjects {{ totalCount }}
    }}
    category {{
      name
      parentCategory {{ name }}
    }}
  }}
}}
"""


_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _extract_emails(*texts: str) -> list[str]:
    """Return unique email addresses found across any of the given text blobs."""
    seen: set[str] = set()
    emails: list[str] = []
    for text in texts:
        for m in _EMAIL_RE.finditer(text or ""):
            addr = m.group(0).lower()
            if addr not in seen:
                seen.add(addr)
                emails.append(addr)
    return emails


def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_module.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_detail(
    pid: int,
    config: Config,
    cache: Cache,
    client: RateLimitedClient,
    no_cache: bool = False,
    verbose: bool = False,
) -> dict | None:
    if not no_cache:
        cached = cache.get_project_detail(pid, config.cache_project_detail_ttl_days)
        if cached is not None:
            if verbose:
                print(f"  [cache] detail {pid}")
            return cached

    if verbose:
        print(f"  [fetch] detail {pid}...")

    try:
        data = client.graphql(_GQL.format(pid=pid))
    except Exception as exc:
        print(f"  Warning: detail fetch failed for {pid}: {exc}")
        return None

    project = (data.get("data") or {}).get("project")
    if not project:
        return None

    creator = project.get("creator") or {}
    category = project.get("category") or {}
    parent_cat = category.get("parentCategory") or {}

    story_text = _strip_html(project.get("story") or "")
    risks_text = _strip_html(project.get("risks") or "")
    desc_text = project.get("description") or ""
    bio_text = creator.get("biography") or ""

    detail = {
        "pid": pid,
        "name": project.get("name", ""),
        "description": desc_text,
        "story_text": story_text,
        "risks_text": risks_text,
        "url": project.get("url", ""),
        "short_url": project.get("projectShortLink") or project.get("url", ""),
        "percent_funded": project.get("percentFunded", 0),
        "backers_count": project.get("backersCount", 0),
        "deadline_at": project.get("deadlineAt", 0),
        "launched_at": project.get("launchedAt", 0),
        "creator_name": creator.get("name", ""),
        "creator_bio": bio_text,
        "creator_projects_count": (creator.get("launchedProjects") or {}).get("totalCount", 1),
        "category_name": category.get("name", ""),
        "parent_category": parent_cat.get("name", ""),
        "emails": _extract_emails(story_text, desc_text, bio_text),
    }

    cache.set_project_detail(pid, detail)
    return detail
