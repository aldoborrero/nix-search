# nix-search

A fast, feature-rich CLI tool for searching NixOS packages, options, and flakes using the search.nixos.org API.

## Features

- **Flexible Search** - Search by package name, program name, version, or description
- **Multiple Search Types** - Packages, NixOS options, and flakes
- **Rich Terminal Output** - Beautiful tables with syntax highlighting
- **Channel Support** - Search across different NixOS channels (unstable, 24.11, 24.05, etc.)
- **Platform Filtering** - Filter results by architecture (x86_64-linux, aarch64-darwin, etc.)
- **JSON Output** - Machine-readable output for scripting and automation
- **Automatic Pager** - Built-in pager for large result sets
- **Fast** - Direct Elasticsearch API queries for instant results

## Installation

### Using Nix Profile

```bash
# Install from this repository
nix profile install github:aldoborrero/nix-search

# Install from local checkout
nix profile install .
```

### Using Nix Flakes

Add to your `flake.nix`:

```nix
{
  inputs.nix-search.url = "github:aldoborrero/nix-search";
}
```

Then include in your system packages:

```nix
environment.systemPackages = [ inputs.nix-search.packages.${system}.default ];
```

### Try Without Installing

```bash
nix run github:aldoborrero/nix-search -- python
```

## Usage

### Basic Search

```bash
# Search for packages by keyword
nix-search python
nix-search "python linter"

# Search by program name (binaries provided)
nix-search -p gcc
nix-search --program gcloud

# Search by package attribute name
nix-search -n python3
nix-search --name "emacsPackages.*"

# Search by version
nix-search golang -v "1.21"
```

### Advanced Filtering

```bash
# Filter by platform/architecture
nix-search --platform x86_64-linux firefox
nix-search --platform aarch64-darwin python3

# Search in specific channel
nix-search -c 24.05 firefox
nix-search --channel unstable python3
```

### Search Types

```bash
# Search NixOS options
nix-search -t options "networking.firewall"
nix-search -t options boot

# Search flakes
nix-search -t flakes wayland
```

### Output Options

```bash
# Show detailed information
nix-search -d python3

# Compact output (no spacing between results)
nix-search --compact python

# Reverse sort order (highest priority at bottom)
nix-search -r python

# JSON output for scripting
nix-search --json python3 | jq '.hits.hits[0]._source.package_attr_name'
```

### Pagination

```bash
# Get more results
nix-search -s 50 python

# Start from offset (for pagination)
nix-search --from 20 --size 20 python

# Control pager
nix-search --no-pager python  # Disable pager
nix-search --pager python     # Force pager
```

## Examples

### Find a Package by Binary Name

```bash
$ nix-search -p terraform
Found 12 results (showing 12)

[1] terraform @ 1.9.8
Programs: terraform
Description: Tool for building, changing, and versioning infrastructure
Install: nix-env -iA nixpkgs.terraform
        nix profile install nixpkgs#terraform
```

### Search NixOS Options

```bash
$ nix-search -t options "services.nginx"
Found 89 results (showing 20)

[1] services.nginx.enable
Type: boolean
Description: Whether to enable nginx.
```

### Script with JSON Output

```bash
# Get latest Python 3 version
nix-search --json -n python3 -s 1 | jq -r '.hits.hits[0]._source.package_pversion'
```

## Development

### Prerequisites

- Nix with flakes enabled
- Python 3.13+

### Build

```bash
nix build
```

### Development Shell

```bash
nix develop
```

### Run Tests

```bash
nix build .#checks.x86_64-linux.default
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

This tool interfaces with the official [search.nixos.org](https://search.nixos.org) API.
