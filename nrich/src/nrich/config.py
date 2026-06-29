"""Configuration loader for nrich."""

from pathlib import Path
import yaml


CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""


class Config:
    """Typed container for nrich configuration."""

    def __init__(self, data: dict):
        apollo = data.get("apollo", {})
        self.apollo_api_key: str = apollo.get("api_key", "")
        self.apollo_rate_limit: int = apollo.get("rate_limit_per_hour", 600)

        google = data.get("google_cse", {})
        self.google_api_key: str = google.get("api_key", "")
        self.google_cx: str = google.get("cx", "")

        search = data.get("search", {})
        self.timeout: int = search.get("timeout", 15)
        self.min_delay: float = search.get("min_delay", 1.0)


def load_config(path: Path = CONFIG_PATH) -> Config:
    """Read and validate config.yaml."""
    if not path.exists():
        raise ConfigError(
            f"Config file not found at {path}\n"
            f"Copy nrich/config.example.yaml to nrich/config.yaml and fill in your API keys."
        )

    with open(path) as f:
        data = yaml.safe_load(f)

    if not data:
        raise ConfigError(f"Config file at {path} is empty or invalid YAML.")

    apollo_key = data.get("apollo", {}).get("api_key", "")
    if not apollo_key or apollo_key == "YOUR_APOLLO_API_KEY_HERE":
        raise ConfigError(
            "Apollo API key is not configured.\n"
            "Set apollo.api_key in nrich/config.yaml"
        )

    return Config(data)
