from __future__ import annotations
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import click
import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .cache import Cache
from .classify import classify_project, check_retry_state, handle_fatal_error
from .classify import _clear_retry_state
from .config import load_config
from .detail import fetch_detail
from .discover import discover_projects
from .http_client import RateLimitedClient
from .output import print_json, print_markdown, print_table, print_yaml
from .output import save_structured, save_text


def _load_dotenv() -> None:
    """Load .env file from common locations so users never need to source it manually."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",   # ks-scout/.env
        Path.home() / ".env",
    ]
    for envfile in candidates:
        try:
            for line in envfile.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                line = line.removeprefix("export ")
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key and val and key not in os.environ:
                    os.environ[key] = val
        except (FileNotFoundError, PermissionError):
            continue
from .score import composite_score, compute_traction, days_remaining


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--categories", default="hardware,gadgets,diy-electronics,sound", show_default=True,
              help="Comma-separated category slugs.")
@click.option("--min-funded-pct", default=51, show_default=True, type=int,
              help="Minimum % funded.")
@click.option("--min-traction", default=1.2, show_default=True, type=float,
              help="Minimum traction score.")
@click.option("--limit", default=20, show_default=True, type=int,
              help="Max rows in final output.")
@click.option("--no-cache", is_flag=True, default=False,
              help="Bypass all caches for this run.")
@click.option("--verbose", is_flag=True, default=False,
              help="Print intermediate scoring and classifier reasoning.")
@click.option("--output", "output_format", default="yaml", show_default=True,
              type=click.Choice(["table", "json", "yaml", "markdown"], case_sensitive=False),
              help="Output format.")
@click.option("--min-pledged-usd", default=50000, show_default=True, type=int,
              help="Minimum USD pledged at time of search.")
@click.option("--ended-within-days", default=7, show_default=True, type=int,
              help="Include ended campaigns that closed within this many days.")
@click.option("--save", "save_path", default=None, type=click.Path(),
              help="Override the accumulated-leads file (default: output/leads.txt).")
@click.option("--append", "append_flag", is_flag=True, default=False,
              help="(DEPRECATED — now always on by default. Kept for compatibility.)")
@click.option("--no-save", "no_save_flag", is_flag=True, default=False,
              help="Skip saving results to disk entirely (console output only).")
@click.option("--config", "config_path", default=None, type=click.Path(),
              help="Config file path (default: ~/.config/ks-scout/config.toml).")
def main(
    categories: str,
    min_funded_pct: int,
    min_traction: float,
    limit: int,
    no_cache: bool,
    verbose: bool,
    output_format: str,
    min_pledged_usd: int,
    ended_within_days: int,
    save_path: str | None,
    append_flag: bool,
    no_save_flag: bool,
    config_path: str | None,
) -> None:
    """Discover live and recently-ended Kickstarter hardware projects that likely need EE help."""
    _load_dotenv()  # auto-load .env so the user never has to source it
    err = Console(stderr=True)

    # Load config
    try:
        config = load_config(Path(config_path) if config_path else None)
    except Exception as exc:
        err.print(f"[red]Config error:[/red] {exc}")
        sys.exit(1)

    # Validate API key before touching the network
    api_key = os.environ.get(config.llm_api_key_env)
    if not api_key:
        err.print(f"[red]Error:[/red] environment variable [bold]{config.llm_api_key_env}[/bold] is not set.")
        err.print(f"Set it with:  export {config.llm_api_key_env}=<your-key>")
        sys.exit(3)

    # Open cache
    try:
        cache = Cache(config.cache_db_path)
    except Exception as exc:
        err.print(f"[red]Cache error:[/red] {exc}")
        sys.exit(1)

    # Warn about pending retries from a previous credit-exhausted run
    retry_warning = check_retry_state()
    if retry_warning:
        err.print(f"[yellow]{retry_warning}[/yellow]")

    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    max_candidates = limit * 5

    with RateLimitedClient(config.http_rate_limit_rps) as client:
        # 1. Discover
        err.print(f"Discovering projects (live + ended ≤{ended_within_days}d) in: {', '.join(cat_list)}…")
        try:
            raw = discover_projects(
                cat_list, config, cache, client,
                max_candidates=max_candidates, ended_within_days=ended_within_days,
                no_cache=no_cache, verbose=verbose,
            )
        except httpx.NetworkError:
            err.print("[red]Network unreachable.[/red]")
            sys.exit(4)
        except httpx.HTTPStatusError as exc:
            err.print(f"[red]Kickstarter API error {exc.response.status_code}[/red]")
            sys.exit(2)

        err.print(f"  {len(raw)} candidates found.")

        # 2. Funding % filter — ended campaigns must also be fully funded (≥100%)
        now_ts = time.time()
        funded = [
            p for p in raw
            if p.get("percent_funded", 0) >= min_funded_pct
            and (p.get("deadline", 0) >= now_ts or p.get("percent_funded", 0) >= 100)
        ]
        if verbose:
            err.print(f"  After funding filter (≥{min_funded_pct}%, ended→≥100%): {len(funded)}")

        # 2b. Country filter — exclude CN and HK
        _EXCLUDED_COUNTRIES = {"CN", "HK"}
        funded = [
            p for p in funded
            if p.get("country", "").upper() not in _EXCLUDED_COUNTRIES
            and (p.get("location") or {}).get("country", "").upper() not in _EXCLUDED_COUNTRIES
        ]
        if verbose:
            err.print(f"  After country filter (excl. CN/HK): {len(funded)}")

        # 2c. Minimum USD pledged filter
        funded = [
            p for p in funded
            if float(p.get("usd_pledged") or 0) >= min_pledged_usd
        ]
        if verbose:
            err.print(f"  After min pledged filter (≥${min_pledged_usd:,}): {len(funded)}")

        # 3. Traction filter
        with_traction = []
        for p in funded:
            t = compute_traction(
                p.get("percent_funded", 0),
                p.get("deadline", 0),
                p.get("launched_at", 0),
            )
            if t >= min_traction:
                p["_traction"] = t
                with_traction.append(p)
        if verbose:
            err.print(f"  After traction filter (≥{min_traction}): {len(with_traction)}")

        # Sort by traction; fetch details for the strongest candidates only
        with_traction.sort(key=lambda p: p["_traction"], reverse=True)
        to_detail = with_traction[:max_candidates]

        # 4. Fetch project details
        detailed: list[dict] = []
        with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                      console=err, transient=True) as prog:
            task = prog.add_task(
                f"Fetching details for {len(to_detail)} projects…",
                total=len(to_detail),
            )
            for p in to_detail:
                pid = p["id"]
                name_preview = p.get("name", str(pid))[:40]
                prog.update(task, advance=1, description=f"Fetching: {name_preview}")

                detail = fetch_detail(
                    pid, config, cache, client, no_cache=no_cache, verbose=verbose,
                )
                if detail is None:
                    continue

                # Merge traction + fallback fields from discovery
                detail["traction"] = p["_traction"]
                if not detail.get("percent_funded"):
                    detail["percent_funded"] = p.get("percent_funded", 0)
                if not detail.get("deadline_at"):
                    detail["deadline_at"] = p.get("deadline", 0)
                if not detail.get("launched_at"):
                    detail["launched_at"] = p.get("launched_at", 0)
                if not detail.get("creator_name"):
                    detail["creator_name"] = (p.get("creator") or {}).get("name", "")
                detail["days_remaining"] = days_remaining(detail["deadline_at"])
                detailed.append(detail)

        # 4b. First-project filter
        detailed = [r for r in detailed if r.get("creator_projects_count", 1) <= 1]
        if verbose:
            err.print(f"  After first-project filter: {len(detailed)}")

        # 5. LLM classify
        err.print(f"Classifying {len(detailed)} projects with {config.llm_model}…")
        fatal_stop = False
        for r in detailed:
            cls = classify_project(r, config, cache, api_key=api_key, verbose=verbose)
            if cls.pop("_fatal", False):
                fatal_stop = True
                r["ee_gap"] = "ERR"
                r["confidence"] = 0.0
                r["evidence"] = cls.get("evidence", "")
                msg = handle_fatal_error(Exception(cls.get("evidence", "unknown")), output_dir="output")
                err.print(f"[red]{msg}[/red]")
                break
            r.update(cls)  # adds ee_gap, confidence, evidence

        # Mark remaining unclassified projects as ERR so ranking doesn't break
        if fatal_stop:
            for r in detailed:
                if "ee_gap" not in r:
                    r["ee_gap"] = "ERR"
                    r["confidence"] = 0.0
                    r["evidence"] = "Skipped — batch aborted due to credit exhaustion"
        else:
            # Successful run — clear any pending credit-exhausted retry state
            _clear_retry_state()

    # 6. Rank
    for r in detailed:
        r["composite_score"] = composite_score(r["traction"], r["ee_gap"], r["confidence"])

    ranked = sorted(
        (r for r in detailed if r.get("ee_gap") not in ("ERR", "LOW") and r.get("composite_score", 0) > 0),
        key=lambda r: r["composite_score"],
        reverse=True,
    )[:limit]

    if not ranked:
        err.print("[yellow]No projects matched all criteria.[/yellow]")
        sys.exit(0)

    # 7. Print
    if output_format == "table":
        print_table(ranked)
        if verbose:
            err.print("\n[dim]Classifier evidence:[/dim]")
            for i, r in enumerate(ranked, 1):
                err.print(f"  {i:2}. [bold]{r.get('name','')[:40]}[/bold] ({r['ee_gap']} {r['confidence']:.0%})")
                err.print(f"      {r.get('evidence', '')}")
    elif output_format == "json":
        print_json(ranked)
    elif output_format == "yaml":
        print_yaml(ranked)
    else:
        print_markdown(ranked)

    # 8. Always save — accumulated + date-stamped snapshot (unless --no-save)
    if not no_save_flag:
        ext = {"yaml": ".yaml", "json": ".json"}.get(output_format, ".txt")
        base_path = save_path or f"output/leads{ext}"
        date_suffix = datetime.now().strftime("%Y%m%d")
        stem = Path(base_path).stem  # e.g. "leads"
        outdir = Path(base_path).parent
        snapshot_path = str(outdir / f"{stem}_{date_suffix}{ext}")

        if output_format in ("yaml", "json"):
            written = save_structured(ranked, base_path, output_format, append=True)
            if written > 0:
                err.print(f"Appended {written} new results to [bold]{base_path}[/bold]")
            else:
                err.print(f"[dim]All {len(ranked)} results already in [bold]{base_path}[/bold], nothing new.[/dim]")
            save_structured(ranked, snapshot_path, output_format)
        else:
            written = save_text(ranked, base_path, append=True)
            if written > 0:
                err.print(f"Appended {written} new results to [bold]{base_path}[/bold]")
            else:
                err.print(f"[dim]All {len(ranked)} results already in [bold]{base_path}[/bold], nothing new.[/dim]")
            save_text(ranked, snapshot_path)

        err.print(f"Current run saved to [bold]{snapshot_path}[/bold]")
