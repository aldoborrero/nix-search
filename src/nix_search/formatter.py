import json
import sys
from io import StringIO
from typing import Any

import click
from rich.console import Console
from rich.table import Table

# Display constants
MAX_PROGRAMS_DISPLAY = 10
MAX_DESCRIPTION_LENGTH = 150
MAX_OPTION_DESCRIPTION_LENGTH = 200
MAX_DEFAULT_LENGTH = 100
MAX_EXAMPLE_LENGTH = 100
PAGER_THRESHOLD = 10


def format_package_result_table(
    source: dict[str, Any], index: int, details: bool = False
) -> Table:
    """Format a single package search result as a table"""
    attr_name = source.get("package_attr_name", "unknown")
    version = source.get("package_pversion", "")
    description = source.get("package_description", "")
    programs = source.get("package_programs", [])

    # Create table
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=12)
    table.add_column("Value", overflow="fold")

    # Package name and version using markup
    if version:
        name_markup = f"[dim]\\[{index}][/dim] [bold cyan]{attr_name}[/bold cyan] [dim]@[/dim] [yellow]{version}[/yellow]"
    else:
        name_markup = f"[dim]\\[{index}][/dim] [bold cyan]{attr_name}[/bold cyan]"
    table.add_row("Package", name_markup)

    # Programs
    if programs:
        programs_str = " ".join(programs[:MAX_PROGRAMS_DISPLAY])
        if len(programs) > MAX_PROGRAMS_DISPLAY:
            programs_str += f" ... (+{len(programs) - MAX_PROGRAMS_DISPLAY} more)"
        table.add_row("Programs", f"[green]{programs_str}[/green]")

    # Description
    if description:
        desc = (
            description[:MAX_DESCRIPTION_LENGTH] + "..."
            if len(description) > MAX_DESCRIPTION_LENGTH
            else description
        )
        table.add_row("Description", desc)

    if details:
        # Additional details
        if homepage := source.get("package_homepage"):
            if isinstance(homepage, list):
                # Make each URL clickable
                clickable_links = [f"[link={url}]{url}[/link]" for url in homepage]
                homepage_str = " ".join(clickable_links)
            else:
                homepage_str = f"[link={homepage}]{homepage}[/link]"
            table.add_row("Homepage", homepage_str)

        if license_name := source.get("package_license_set"):
            licenses = ", ".join(license_name[:3])
            table.add_row("License", f"[magenta]{licenses}[/magenta]")

        if maintainers := source.get("package_maintainers"):
            maint_names = [m.get("name", m.get("email", "")) for m in maintainers[:3]]
            maint_str = ", ".join(maint_names)
            table.add_row("Maintainers", f"[cyan]{maint_str}[/cyan]")

    # Installation commands with syntax highlighting
    table.add_row("Install", f"[dim]nix-env -iA nixpkgs.{attr_name}[/dim]")
    table.add_row("", f"[dim]nix profile install nixpkgs#{attr_name}[/dim]")

    return table


def format_option_result_table(
    source: dict[str, Any], index: int, details: bool = False
) -> Table:
    """Format a single option search result as a table"""
    option_name = source.get("option_name", "unknown")
    option_type = source.get("option_type", "")
    description = source.get("option_description", "")
    default = source.get("option_default")
    example = source.get("option_example")

    # Create table
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold magenta", width=12)
    table.add_column("Value", overflow="fold")

    # Option name using markup
    name_markup = f"[dim]\\[{index}][/dim] [bold magenta]{option_name}[/bold magenta]"
    table.add_row("Option", name_markup)

    if option_type:
        table.add_row("Type", f"[cyan]{option_type}[/cyan]")

    if description:
        desc = (
            description[:MAX_OPTION_DESCRIPTION_LENGTH] + "..."
            if len(description) > MAX_OPTION_DESCRIPTION_LENGTH
            else description
        )
        table.add_row("Description", desc)

    if details:
        if default:
            default_str = str(default)[:MAX_DEFAULT_LENGTH]
            table.add_row("Default", f"[yellow]{default_str}[/yellow]")
        if example:
            example_str = str(example)[:MAX_EXAMPLE_LENGTH]
            table.add_row("Example", f"[green]{example_str}[/green]")

    return table


def _render_results(
    console: Console,
    hits: list[dict[str, Any]],
    search_type: str,
    total_value: int,
    details: bool,
    compact: bool,
) -> None:
    """Render results to a console (helper to avoid duplication)"""
    console.print(
        f"\n[bold green]Found {total_value} results[/bold green] [dim](showing {len(hits)})[/dim]\n"
    )

    for i, hit in enumerate(hits, 1):
        source = hit.get("_source", {})
        if search_type == "packages" or search_type == "flakes":
            table = format_package_result_table(source, i, details)
        elif search_type == "options":
            table = format_option_result_table(source, i, details)
        else:
            continue

        console.print(table)
        # In compact mode, don't add spacing between results
        if not compact and i < len(hits):
            console.print()


def _output_with_pager(content: str) -> None:
    """Send content to pager"""
    click.echo_via_pager(content)


def print_results(
    data: dict[str, Any],
    search_type: str,
    details: bool = False,
    compact: bool = False,
    json_output: bool = False,
    reverse: bool = False,
    use_pager: bool | None = None,
) -> None:
    """Print search results

    Args:
        data: Search results data
        search_type: Type of search (packages, options, flakes)
        details: Show detailed information
        compact: Show in compact table format
        json_output: Output raw JSON
        reverse: Reverse sort order
        use_pager: Control pager usage (None=auto, True=force, False=disable)
    """
    if json_output:
        output = json.dumps(data, indent=2)
        if use_pager:
            _output_with_pager(output)
        else:
            print(output)
        return

    hits = data.get("hits", {}).get("hits", [])
    total = data.get("hits", {}).get("total", {})
    total_value = total.get("value", 0) if isinstance(total, dict) else total

    if not hits:
        Console().print("[yellow]No results found.[/yellow]")
        return

    # Reverse the order if requested
    if reverse:
        hits = list(reversed(hits))

    # Determine if we should use pager
    # Auto-detect: use pager if more than threshold results or if explicitly requested
    should_use_pager = (
        use_pager if use_pager is not None else len(hits) > PAGER_THRESHOLD
    )

    if should_use_pager and sys.stdout.isatty():
        # Render to string buffer for pager
        string_buffer = StringIO()
        console = Console(file=string_buffer, force_terminal=True)
        _render_results(console, hits, search_type, total_value, details, compact)
        _output_with_pager(string_buffer.getvalue())
    else:
        # Direct output (no pager)
        console = Console()
        _render_results(console, hits, search_type, total_value, details, compact)
