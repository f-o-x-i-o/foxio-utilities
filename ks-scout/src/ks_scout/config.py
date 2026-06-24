from __future__ import annotations
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    llm_api_key_env: str = "DEEPSEEK_API_KEY"
    cache_project_list_ttl_hours: int = 6
    cache_project_detail_ttl_days: int = 7
    cache_db_path: Path = Path("~/.cache/ks-scout/cache.db")
    http_user_agent: str = "ks-scout/0.1 (personal research tool)"
    http_rate_limit_rps: float = 1.0


def load_config(path: Path | None = None) -> Config:
    config_path = path or Path("~/.config/ks-scout/config.toml").expanduser()

    raw: dict = {}
    if config_path.exists():
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)

    llm = raw.get("llm", {})
    cache = raw.get("cache", {})
    http = raw.get("http", {})

    return Config(
        llm_provider=llm.get("provider", "deepseek"),
        llm_model=llm.get("model", "deepseek-chat"),
        llm_api_key_env=llm.get("api_key_env", "DEEPSEEK_API_KEY"),
        cache_project_list_ttl_hours=cache.get("project_list_ttl_hours", 6),
        cache_project_detail_ttl_days=cache.get("project_detail_ttl_days", 7),
        cache_db_path=Path(cache.get("db_path", "~/.cache/ks-scout/cache.db")).expanduser(),
        http_user_agent=http.get("user_agent", "ks-scout/0.1 (personal research tool)"),
        http_rate_limit_rps=float(http.get("rate_limit_rps", 1.0)),
    )
