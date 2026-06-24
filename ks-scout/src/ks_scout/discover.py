from __future__ import annotations
import time
from .cache import Cache
from .config import Config
from .http_client import RateLimitedClient

CATEGORY_IDS: dict[str, int] = {
    "hardware": 52,
    "gadgets": 337,
    "diy-electronics": 334,
    "sound": 339,
    "wearables": 341,
    "3d-printing": 331,
    "robots": 338,
    "software": 51,
    "technology": 16,
}

def _fetch_category(
    client: RateLimitedClient,
    category: str,
    max_results: int,
    ended_within_days: int = 7,
    state: str = "live",
    sort: str = "popularity",
) -> list[dict]:
    cat_id = CATEGORY_IDS.get(category)
    if cat_id is None:
        valid = ", ".join(CATEGORY_IDS)
        raise ValueError(f"Unknown category {category!r}. Valid options: {valid}")

    cutoff = time.time() - ended_within_days * 86400

    projects: list[dict] = []
    page = 1
    while len(projects) < max_results:
        data = client.get_json(
            "https://www.kickstarter.com/discover/advanced",
            params={
                "category_id": cat_id,
                "format": "json",
                "state": state,
                "page": page,
                "per_page": 40,
                "sort": sort,
            },
        )
        batch = data.get("projects", [])
        if not batch:
            break

        for p in batch:
            # For ended campaigns, stop paginating once we're past 7 days
            if state != "live":
                deadline = p.get("deadline", 0)
                if deadline < cutoff:
                    return projects[:max_results]
            projects.append(p)

        if not data.get("has_more", False):
            break
        page += 1

    return projects[:max_results]


def discover_projects(
    categories: list[str],
    config: Config,
    cache: Cache,
    client: RateLimitedClient,
    max_candidates: int,
    ended_within_days: int = 7,
    no_cache: bool = False,
    verbose: bool = False,
) -> list[dict]:
    seen: dict[int, dict] = {}
    cutoff = time.time() - ended_within_days * 86400

    for category in categories:
        for state, sort, cache_key in [
            ("live",       "popularity", category),
            ("successful", "end_date",   f"{category}_recent_successful"),
        ]:
            cached = None if no_cache else cache.get_project_list(
                cache_key, config.cache_project_list_ttl_hours
            )
            if cached is not None:
                if verbose:
                    print(f"  [cache] '{cache_key}': {len(cached)} projects")
                projects = cached
            else:
                if verbose:
                    print(f"  [fetch] '{cache_key}' (state={state})...")
                projects = _fetch_category(
                    client, category, max_candidates,
                    ended_within_days=ended_within_days, state=state, sort=sort,
                )
                if state != "live":
                    projects = [p for p in projects if p.get("deadline", 0) >= cutoff]
                cache.set_project_list(cache_key, projects)
                if verbose:
                    print(f"  [fetch] '{cache_key}': {len(projects)} projects")

            for p in projects:
                pid = p.get("id")
                if pid and pid not in seen:
                    seen[pid] = p

    return list(seen.values())
