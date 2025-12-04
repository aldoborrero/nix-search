import json
import sys
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

# API constants
SCHEMA_VERSION = 44
REQUEST_TIMEOUT = 30
MAX_RESULTS = 10000  # Elasticsearch limit


class NixOSSearchClient:
    """Client for interacting with search.nixos.org Elasticsearch API"""

    # Default credentials
    DEFAULT_USERNAME = "aWVSALXpZv"
    DEFAULT_PASSWORD = "X8gPHnzL52wFEekuxsfQ9cSh"

    def __init__(
        self,
        base_url: str = "https://search.nixos.org",
        username: str | None = None,
        password: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username or self.DEFAULT_USERNAME
        self.password = password or self.DEFAULT_PASSWORD

    def _build_query(
        self,
        query: str,
        name: str | None = None,
        program: str | None = None,
        version: str | None = None,
        platform: str | None = None,
        search_type: str = "packages",
    ) -> dict[str, Any]:
        """Build Elasticsearch query"""

        must_clauses = []

        # Default multi-match query (like the web interface)
        if query:
            must_clauses.append(
                {
                    "dis_max": {
                        "queries": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "type": "cross_fields",
                                    "fields": [
                                        "package_attr_name^9",
                                        "package_attr_name.*^5.3999999999999995",
                                        "package_programs^9",
                                        "package_programs.*^5.3999999999999995",
                                        "package_pname^6",
                                        "package_pname.*^3.5999999999999996",
                                        "package_description^1.3",
                                        "package_description.*^0.78",
                                        "package_longDescription^1",
                                        "package_longDescription.*^0.6",
                                        "flake_name^0.5",
                                    ]
                                    if search_type == "packages"
                                    else ["option_name^2", "option_description"],
                                }
                            }
                        ]
                    }
                }
            )

        # Specific field searches
        if name:
            must_clauses.append({"wildcard": {"package_attr_name": f"*{name}*"}})  # type: ignore[dict-item]

        if program:
            must_clauses.append({"wildcard": {"package_programs": f"*{program}*"}})  # type: ignore[dict-item]

        if version:
            must_clauses.append({"wildcard": {"package_pversion": f"*{version}*"}})  # type: ignore[dict-item]

        if platform:
            must_clauses.append({"term": {"package_platforms": platform}})  # type: ignore[dict-item]

        # Build final query
        es_query = {
            "query": {
                "bool": {"must": must_clauses if must_clauses else [{"match_all": {}}]}
            }
        }

        return es_query

    def search(
        self,
        query: str = "",
        name: str | None = None,
        program: str | None = None,
        version: str | None = None,
        platform: str | None = None,
        channel: str = "unstable",
        search_type: str = "packages",
        size: int = 20,
        from_: int = 0,
    ) -> dict[str, Any]:
        """
        Search using search.nixos.org Elasticsearch API

        Args:
            query: Default search query (searches across multiple fields)
            name: Search by package attribute name
            program: Search by installed programs
            version: Search by package version
            platform: Filter by platform/architecture (e.g., x86_64-linux, aarch64-darwin)
            channel: NixOS channel (unstable, 24.05, 23.11, etc.)
            search_type: Type of search (packages, options, flakes)
            size: Number of results to return
            from_: Starting offset for pagination

        Returns:
            API response as dictionary
        """
        # Determine the correct index based on channel and type
        if search_type == "flakes":
            index = f"latest-{SCHEMA_VERSION}-nixos-flakes"
        elif search_type == "options":
            if channel == "unstable":
                index = f"latest-{SCHEMA_VERSION}-nixos-unstable-options"
            else:
                index = f"latest-{SCHEMA_VERSION}-nixos-{channel}-options"
        else:  # packages
            if channel == "unstable":
                index = f"latest-{SCHEMA_VERSION}-nixos-unstable"
            else:
                index = f"latest-{SCHEMA_VERSION}-nixos-{channel}"

        endpoint = f"{self.base_url}/backend/{index}/_search"

        # Build query
        es_query = self._build_query(
            query, name, program, version, platform, search_type
        )
        es_query["size"] = size
        es_query["from"] = from_

        # Add sorting
        es_query["sort"] = (
            [{"_score": "desc"}, {"package_attr_name": "desc"}]
            if search_type == "packages"
            else [{"_score": "desc"}]
        )

        try:
            auth = HTTPBasicAuth(self.username, self.password)
            response = requests.post(
                endpoint, json=es_query, auth=auth, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}", file=sys.stderr)
            sys.exit(1)
