from __future__ import annotations
import json
import re
from pathlib import Path

import yaml
from rich import box
from rich.console import Console
from rich.table import Table


def _trunc(s: str, n: int) -> str:
    return s[: n - 1] + "…" if len(s) > n else s


def _gap_style(ee_gap: str) -> str:
    return {"HIGH": "bold red", "MED": "yellow", "LOW": "green", "ERR": "dim"}.get(ee_gap, "")


# ── canonical record used by YAML/JSON print + save ──────────────────────

def _make_record(i: int, r: dict) -> dict:
    return {
        "rank": i,
        "name": r.get("name", ""),
        "creator": r.get("creator_name", ""),
        "team": r.get("team", []),
        "emails": r.get("emails", []),
        "percent_funded": r.get("percent_funded", 0),
        "days_remaining": r.get("days_remaining", 0),
        "traction": round(r.get("traction", 0), 2),
        "ee_gap": r.get("ee_gap", ""),
        "confidence": round(r.get("confidence", 0), 2),
        "composite_score": round(r.get("composite_score", 0), 3),
        "evidence": r.get("evidence", ""),
        "url": r.get("url", ""),
        "short_url": r.get("short_url", ""),
    }


# ── console output ───────────────────────────────────────────────────────

def print_table(results: list[dict], console: Console | None = None) -> None:
    con = console or Console()
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    t.add_column("Rank", justify="right", width=4)
    t.add_column("Project", width=33)
    t.add_column("Creator", width=18)
    t.add_column("%Fund", justify="right", width=6)
    t.add_column("Days", justify="right", width=5)
    t.add_column("Tract", justify="right", width=5)
    t.add_column("EE-Gap", width=7)
    t.add_column("URL")

    for i, r in enumerate(results, 1):
        gap = r.get("ee_gap", "?")
        style = _gap_style(gap)
        t.add_row(
            str(i),
            _trunc(r.get("name", ""), 32),
            _trunc(r.get("creator_name", ""), 18),
            f"{r.get('percent_funded', 0):.0f}%",
            str(r.get("days_remaining", 0)),
            f"{r.get('traction', 0):.1f}",
            f"[{style}]{gap}[/{style}]",
            r.get("short_url", r.get("url", "")),
        )
    con.print(t)


def print_json(results: list[dict]) -> None:
    out = [_make_record(i, r) for i, r in enumerate(results, 1)]
    print(json.dumps(out, indent=2, ensure_ascii=False))


def print_yaml(results: list[dict]) -> None:
    out = [_make_record(i, r) for i, r in enumerate(results, 1)]
    print(
        yaml.dump(
            out,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=120,
        ).strip()
    )


def print_markdown(results: list[dict]) -> None:
    print("| Rank | Project | Creator | %Fund | Days | Tract | EE-Gap | URL |")
    print("|------|---------|---------|-------|------|-------|--------|-----|")
    for i, r in enumerate(results, 1):
        print(
            f"| {i} | {_trunc(r.get('name',''), 32)} | {r.get('creator_name','')} "
            f"| {r.get('percent_funded',0):.0f}% | {r.get('days_remaining',0)} "
            f"| {r.get('traction',0):.1f} | {r.get('ee_gap','')} "
            f"| {r.get('short_url', r.get('url',''))} |"
        )


# ── file persistence (format-aware) ──────────────────────────────────────

_EXTENSIONS = {"yaml": ".yaml", "json": ".json", "table": ".txt", "markdown": ".txt"}


def _url_key(r: dict) -> str:
    return r.get("short_url") or r.get("url", "")


def _load_structured(path: str, fmt: str) -> list[dict]:
    """Load existing records from a YAML/JSON file. Returns [] if missing/invalid."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    try:
        if fmt == "yaml":
            data = yaml.safe_load(raw)
            return data if isinstance(data, list) else []
        else:  # json
            data = json.loads(raw)
            return data if isinstance(data, list) else []
    except (yaml.YAMLError, json.JSONDecodeError, ValueError):
        return []


def _existing_urls_text(path: str) -> set[str]:
    """Extract URLs from a legacy text-format file."""
    urls: set[str] = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^\s*URL:\s+(.+?)\s*$", line)
                if m:
                    urls.add(m.group(1))
    except FileNotFoundError:
        pass
    return urls


def _existing_urls_structured(path: str, fmt: str) -> set[str]:
    """Extract URLs from a YAML/JSON file."""
    return {_url_key(r) for r in _load_structured(path, fmt) if _url_key(r)}


def save_structured(results: list[dict], path: str, fmt: str, append: bool = False) -> int:
    """Save results in YAML or JSON format.

    If *append* is True, existing entries are preserved, duplicates are skipped,
    numbering continues, and the file is re-written as a single array.
    Returns the number of *new* entries written (0 if all duplicates).
    """
    outdir = Path(path).parent
    outdir.mkdir(parents=True, exist_ok=True)

    if append:
        existing = _load_structured(path, fmt)
        existing_urls = {_url_key(r) for r in existing if _url_key(r)}
        new_records = [
            _make_record(i, r)
            for i, r in enumerate(results, 1)
            if _url_key(r) not in existing_urls
        ]
        if not new_records:
            return 0
        merged = existing + new_records
    else:
        merged = [_make_record(i, r) for i, r in enumerate(results, 1)]
        new_records = merged

    # Re-number
    for idx, rec in enumerate(merged, 1):
        rec["rank"] = idx

    if fmt == "yaml":
        content = yaml.dump(
            merged, allow_unicode=True, default_flow_style=False,
            sort_keys=False, width=120,
        )
    else:
        content = json.dumps(merged, indent=2, ensure_ascii=False)

    Path(path).write_text(content, encoding="utf-8")
    return len(new_records)


# ── legacy text format (kept for table/markdown output, because YAML
#    serialisation of every field is annoying for quick reading) ────────────

def _count_entries_in_file(path: str) -> int:
    """Count existing entries in a text save file (lines matching '  N. ')."""
    count = 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if re.match(r"^\s*\d+\.\s", line):
                    count += 1
    except FileNotFoundError:
        pass
    return count


def save_text(results: list[dict], path: str, append: bool = False) -> int:
    """Write untruncated text to a plain-text file.  Used for table/markdown formats."""
    outdir = Path(path).parent
    outdir.mkdir(parents=True, exist_ok=True)

    if append:
        existing_urls = _existing_urls_text(path)
        new_results = [
            r for r in results
            if _url_key(r) not in existing_urls
        ]
        if not new_results:
            return 0

        start_index = _count_entries_in_file(path) + 1
        write_mode = "a"
    else:
        new_results = results
        start_index = 1
        write_mode = "w"

    with open(path, write_mode, encoding="utf-8") as f:
        if write_mode == "w":
            f.write(f"ks-scout results — {len(new_results)} projects\n")
            f.write("=" * 60 + "\n\n")
        elif append and start_index == 1:
            f.write(f"ks-scout results — {len(new_results)} projects\n")
            f.write("=" * 60 + "\n\n")

        for i, r in enumerate(new_results, start_index):
            f.write(f"{i:2}. {r.get('name', '')}\n")
            f.write(f"    Creator:  {r.get('creator_name', '')}\n")
            team = r.get("team", [])
            if team:
                for member in team:
                    f.write(f"    Team:     {member}\n")
            emails = r.get("emails", [])
            for email in emails:
                f.write(f"    Email:    {email}\n")
            f.write(f"    Funded:   {r.get('percent_funded', 0):.0f}%  |  "
                    f"Days left: {r.get('days_remaining', 0)}  |  "
                    f"Traction: {r.get('traction', 0):.1f}  |  "
                    f"EE-Gap: {r.get('ee_gap', '')}\n")
            f.write(f"    URL:      {r.get('short_url', r.get('url', ''))}\n")
            if r.get("evidence"):
                f.write(f"    Evidence: {r['evidence']}\n")
            f.write("\n")

    if append and new_results:
        total = start_index + len(new_results) - 1
        _update_header_count(path, total)

    return len(new_results)


def _update_header_count(path: str, total: int) -> None:
    """Replace the first line of the file with the correct project count."""
    try:
        with open(path, "r+", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                lines[0] = f"ks-scout results — {total} projects\n"
                f.seek(0)
                f.writelines(lines)
                f.truncate()
    except OSError:
        pass
