"""
llm-surgeon CLI — analyze and optimize your LLM prompts from the terminal.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .surgeon import Surgeon, PRICING
from .scanner import scan_file, scan_directory

app = typer.Typer(
    name="llm-surgeon",
    help="🔪 Cut your LLM API bill by 30–70%. No accuracy loss.",
    add_completion=False,
)
console = Console()


def _make_surgeon(model: str, aggressiveness: str) -> Surgeon:
    return Surgeon(model=model, aggressiveness=aggressiveness)


@app.command()
def analyze(
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="File to analyze"),
    directory: Optional[Path] = typer.Option(None, "--dir", "-d", help="Directory to scan"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recurse into subdirectories"),
    model: str = typer.Option("gpt-4o", "--model", "-m", help="LLM model for pricing"),
    aggressiveness: str = typer.Option("balanced", "--aggressiveness", "-a", help="conservative|balanced|aggressive"),
    calls_per_day: int = typer.Option(1000, "--calls-per-day", help="Daily API calls for cost projection"),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Analyze prompts and show token savings potential."""
    surgeon = _make_surgeon(model, aggressiveness)

    if file:
        prompts = scan_file(file)
    elif directory:
        prompts = scan_directory(directory, recursive=recursive)
    else:
        console.print("[red]Error:[/red] Provide --file or --dir")
        raise typer.Exit(1)

    if not prompts:
        console.print("[yellow]No prompt strings found.[/yellow]")
        raise typer.Exit(0)

    results = [(name, surgeon.optimize(text)) for name, text in prompts]

    if output_json:
        out = [
            {
                "name": name,
                "original_tokens": r.original_tokens,
                "optimized_tokens": r.optimized_tokens,
                "savings_pct": r.savings_pct,
                "monthly_savings_usd": r.monthly_savings_usd(calls_per_day),
                "techniques": r.techniques_applied,
            }
            for name, r in results
        ]
        print(json.dumps(out, indent=2))
        return

    console.print()
    console.print(Panel.fit("[bold]📊 Token Analysis Report[/bold]", border_style="green"))
    console.print()

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("Prompt / Variable", style="white", min_width=24)
    table.add_column("Original", justify="right")
    table.add_column("Optimized", justify="right")
    table.add_column("Saved", justify="right", style="green")
    table.add_column(f"💰 /1k calls ({model})", justify="right", style="yellow")

    total_orig = total_opt = 0
    for name, r in results:
        saving_str = f"-{r.savings_pct}%" if r.savings_pct > 0 else "–"
        cost_str = f"${r.monthly_savings_usd(1000):.2f}"
        table.add_row(name, str(r.original_tokens), str(r.optimized_tokens), saving_str, cost_str)
        total_orig += r.original_tokens
        total_opt += r.optimized_tokens

    console.print(table)

    total_pct = round((1 - total_opt / total_orig) * 100, 1) if total_orig else 0
    surgeon_total = Surgeon(model=model)
    dummy = surgeon_total.optimize(" " * total_orig)
    from .surgeon import PRICING
    price = PRICING.get(model, {}).get("input", 2.50)
    saved_tokens = total_orig - total_opt
    monthly = round(saved_tokens / 1_000_000 * price * calls_per_day * 30, 2)

    console.print()
    console.print(f"  [bold green]TOTAL:[/bold green] {total_pct}% reduction · [yellow]${monthly:,.2f}/month[/yellow] at {calls_per_day:,} calls/day")
    console.print()


@app.command()
def optimize(
    file: Path = typer.Option(..., "--file", "-f", help="File to optimize"),
    preview: bool = typer.Option(False, "--preview", help="Preview changes only"),
    apply: bool = typer.Option(False, "--apply", help="Write changes to file"),
    model: str = typer.Option("gpt-4o", "--model", "-m"),
    aggressiveness: str = typer.Option("balanced", "--aggressiveness", "-a"),
):
    """Optimize prompts in a file. Use --preview to dry-run."""
    surgeon = _make_surgeon(model, aggressiveness)
    prompts = scan_file(file)

    if not prompts:
        console.print("[yellow]No prompt strings found.[/yellow]")
        raise typer.Exit(0)

    console.print()
    for name, text in prompts:
        result = surgeon.optimize(text)
        if result.savings_pct == 0:
            continue
        console.print(f"[bold]{name}[/bold]  {result.original_tokens}→{result.optimized_tokens} tokens  ([green]-{result.savings_pct}%[/green])")
        if preview:
            console.print(Panel(result.optimized_text, title="Optimized", border_style="green"))

    if apply:
        console.print("[yellow]⚠ --apply file rewriting coming in v0.2[/yellow]")
    elif not preview:
        console.print("\nRun with [bold]--preview[/bold] to see changes or [bold]--apply[/bold] to write them.")


@app.command()
def report(
    file: Path = typer.Option(..., "--file", "-f"),
    model: str = typer.Option("gpt-4o", "--model", "-m"),
    calls_per_day: int = typer.Option(1000, "--calls-per-day"),
    aggressiveness: str = typer.Option("balanced", "--aggressiveness", "-a"),
):
    """Generate a full cost savings report."""
    surgeon = _make_surgeon(model, aggressiveness)
    prompts = scan_file(file)

    if not prompts:
        console.print("[yellow]No prompt strings found.[/yellow]")
        raise typer.Exit(0)

    total_monthly = sum(
        surgeon.optimize(text).monthly_savings_usd(calls_per_day)
        for _, text in prompts
    )

    console.print()
    console.print(Panel.fit(
        f"[bold green]💰 Projected monthly savings: ${total_monthly:,.2f}[/bold green]\n"
        f"[dim]Model: {model} · {calls_per_day:,} calls/day · {len(prompts)} prompts analyzed[/dim]",
        border_style="green",
    ))
    console.print()


def main():
    app()


if __name__ == "__main__":
    main()
