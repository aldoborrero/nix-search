from typing import Any

import click

from nix_search.client import MAX_RESULTS, NixOSSearchClient
from nix_search.formatter import print_results


# Completion helpers
def complete_platforms(ctx: Any, param: Any, incomplete: str) -> list[str]:
    """Provide platform completion suggestions"""
    platforms = [
        "x86_64-linux",
        "aarch64-linux",
        "aarch64-darwin",
        "x86_64-darwin",
        "i686-linux",
        "armv7l-linux",
        "riscv64-linux",
        "powerpc64le-linux",
    ]
    return [p for p in platforms if p.startswith(incomplete)]


def complete_channels(ctx: Any, param: Any, incomplete: str) -> list[str]:
    """Provide channel completion suggestions"""
    channels = ["unstable", "24.11", "24.05", "23.11", "23.05"]
    return [c for c in channels if c.startswith(incomplete)]


@click.command()
@click.argument("query", required=False, default="")
@click.option(
    "-n",
    "--name",
    help="Search by package attribute name (supports wildcards)",
)
@click.option(
    "-p",
    "--program",
    help="Search by installed program name (supports wildcards)",
)
@click.option(
    "-v",
    "--version",
    help="Filter by package version (supports wildcards)",
)
@click.option(
    "--platform",
    shell_complete=complete_platforms,
    help="Filter by platform/architecture (e.g., x86_64-linux, aarch64-darwin)",
)
@click.option(
    "-c",
    "--channel",
    default="unstable",
    show_default=True,
    shell_complete=complete_channels,
    help="NixOS channel to search (unstable, 24.05, 24.11, etc.)",
)
@click.option(
    "-t",
    "--type",
    "search_type",
    type=click.Choice(["packages", "options", "flakes"], case_sensitive=False),
    default="packages",
    show_default=True,
    help="Type of search",
)
@click.option(
    "-s",
    "--size",
    type=int,
    default=20,
    show_default=True,
    help="Number of results to return",
)
@click.option(
    "-f",
    "--from",
    "from_",
    type=int,
    default=0,
    show_default=True,
    help="Starting offset for pagination",
)
@click.option(
    "-d",
    "--details",
    is_flag=True,
    help="Show detailed information for each result",
)
@click.option(
    "--compact",
    is_flag=True,
    help="Show results in compact format (no spacing between results)",
)
@click.option(
    "-r",
    "--reverse",
    is_flag=True,
    help="Reverse the sort order (highest priority at bottom)",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output raw JSON response",
)
@click.option(
    "--pager/--no-pager",
    default=None,
    help="Control pager usage (auto-detected by default based on output size)",
)
@click.option(
    "--base-url",
    default="https://search.nixos.org",
    show_default=True,
    help="search.nixos.org instance URL",
)
def main(
    query: str,
    name: str | None,
    program: str | None,
    version: str | None,
    platform: str | None,
    channel: str,
    search_type: str,
    size: int,
    from_: int,
    details: bool,
    compact: bool,
    reverse: bool,
    json_output: bool,
    pager: bool | None,
    base_url: str,
) -> None:
    """CLI tool to search NixOS packages and options using search.nixos.org

    \b
    Examples:
      # Search for packages
      nix-search python
      nix-search "python linter"

      # Search by program name
      nix-search -p gcc
      nix-search --program "gcloud"

      # Search by package name
      nix-search -n python3
      nix-search --name "emacsPackages.*"

      # Search by version
      nix-search golang -v "1.21"

      # Filter by platform
      nix-search --platform x86_64-linux firefox
      nix-search --platform aarch64-darwin python3

      # Search in specific channel
      nix-search -c 24.05 firefox
      nix-search --channel unstable python3

      # Search NixOS options
      nix-search -t options "networking.firewall"

      # Search flakes
      nix-search -t flakes wayland

      # Show detailed information
      nix-search -d python3

      # Reverse sort order (highest priority at bottom)
      nix-search -r python

      # JSON output for scripting
      nix-search --json python3 | jq '.hits.hits[0]._source.package_attr_name'
    """
    if not any([query, name, program, version]):
        raise click.UsageError(
            "At least one of: QUERY, --name, --program, or --version must be specified"
        )

    # Validate pagination parameters
    if size <= 0:
        raise click.BadParameter("size must be greater than 0", param_hint="--size")

    if from_ < 0:
        raise click.BadParameter("from must be non-negative", param_hint="--from")

    if from_ + size > MAX_RESULTS:
        raise click.BadParameter(
            f"from + size cannot exceed {MAX_RESULTS} (Elasticsearch limit)",
            param_hint="--from/--size",
        )

    client = NixOSSearchClient(base_url=base_url)

    data = client.search(
        query=query,
        name=name,
        program=program,
        version=version,
        platform=platform,
        channel=channel,
        search_type=search_type,
        size=size,
        from_=from_,
    )

    print_results(
        data,
        search_type,
        details=details,
        compact=compact,
        json_output=json_output,
        reverse=reverse,
        use_pager=pager,
    )
