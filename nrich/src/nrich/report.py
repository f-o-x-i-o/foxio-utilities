"""Console report for nrich enrichment results."""

import time
from dataclasses import dataclass, field


@dataclass
class EnrichmentStats:
    """Aggregated enrichment statistics."""
    total: int = 0
    apollo: int = 0
    linkedin: int = 0
    web_search: int = 0
    discarded: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def enriched(self) -> int:
        return self.apollo + self.linkedin + self.web_search

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time


def print_report(stats: EnrichmentStats) -> None:
    """Print a formatted enrichment report to stdout."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()

    table = Table(title="nrich — Enrichment Report")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")

    table.add_row("Total leads", str(stats.total))
    table.add_row("Enriched via Apollo", str(stats.apollo))
    table.add_row("Enriched via LinkedIn", str(stats.linkedin))
    table.add_row("Enriched via web search", str(stats.web_search))
    table.add_row("Discarded (no contact)", str(stats.discarded))
    table.add_row("Enriched total", str(stats.enriched))
    table.add_row("Time elapsed", f"{stats.elapsed:.1f}s")

    console.print()
    console.print(table)
    console.print()

    if stats.enriched == 0:
        console.print(
            Panel(
                "[bold yellow]No leads were enriched. Check your API keys or input file.[/]",
                title="⚠ Warning",
            )
        )
    else:
        success_rate = (stats.enriched / stats.total) * 100 if stats.total > 0 else 0
        console.print(
            Panel(
                f"[bold green]Success rate: {success_rate:.0f}% ({stats.enriched}/{stats.total})[/]",
            )
        )
    console.print()
