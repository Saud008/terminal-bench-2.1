""" OpenAPI export staging and JWT scope enforcement."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import yaml

from http_helpers import admin_get, ingest_deck, proxy_request, rebuild, start_daemon, stop_daemon
from reference_export import scope_allows, staged_headers

APP = Path("/app")
FIXTURES = APP / "fixtures"
CATALOG = json.loads((Path(__file__).parent / "catalog_m3.json").read_text(encoding="utf-8"))
SEED = os.environ.get("VERIFIER_SEED", CATALOG["seed"])


def seed_offset(seed: str, label: str) -> int:
    return int(hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()[:8], 16)


def per_run_consumer_key(seed: str) -> str:
    return f"consumer-{seed_offset(seed, 'jwt') & 0xFFFFFF:06x}"


def hidden_scope_deck(seed: str, tmp: Path) -> Path:
    token = format(seed_offset(seed, "scope") % 10000, "04x")
    reader_key = per_run_consumer_key(seed)
    deck = {
        "services": [
            {
                "name": f"scope-svc-{token}",
                "url": "http://127.0.0.1:8000/upstream/scope",
                "plugins": [],
            }
        ],
        "routes": [
            {
                "name": f"scope-route-{token}",
                "service": f"scope-svc-{token}",
                "paths": [f"/api/scope/{token}"],
                "methods": ["GET"],
                "scope_tags": ["inventory:read"],
                "tags": ["public"],
                "plugins": [{"name": "jwt"}],
            }
        ],
        "consumers": [
            {
                "username": f"reader-{token}",
                "jwt": {"key": reader_key, "scopes": ["inventory:read"]},
            },
            {
                "username": f"tag-trap-{token}",
                "jwt": {"key": f"trap-{token}", "scopes": ["public"]},
            },
        ],
    }
    dest = tmp / f"scope-deck-{token}.yaml"
    dest.write_text(yaml.safe_dump(deck), encoding="utf-8")
    return dest


class TestMilestone3:
    def setup_method(self) -> None:
        stop_daemon()
        rebuild()
        start_daemon()
        ingest_deck(FIXTURES / CATALOG["deck_fixture"])

    def teardown_method(self) -> None:
        stop_daemon()

    def test_openapi_includes_plugin_enforced_headers(self) -> None:
        """Export lists merged transformer and rate-limit response headers."""
        status, spec = admin_get("/admin/export/openapi")
        assert status == 200
        path_item = spec["paths"][CATALOG["export_path"]]
        headers = path_item["get"]["responses"]["200"]["headers"]
        deck = yaml.safe_load((FIXTURES / CATALOG["deck_fixture"]).read_text(encoding="utf-8"))
        svc = next(s for s in deck["services"] if s["name"] == "catalog-svc")
        rt = next(r for r in deck["routes"] if r["name"] == "catalog-root-get")
        expected = staged_headers(svc.get("plugins") or [], rt.get("plugins") or [])
        for name in expected:
            assert name in headers

    def test_scope_tags_not_metadata_tags_authorize(self) -> None:
        """Reader JWT passes catalog-items-get via scope_tags, not route tags."""
        status, _, _ = proxy_request(
            "GET",
            "/api/v2/catalog/items",
            bearer=CATALOG["reader_key_field"],
        )
        assert status == 200

    def test_metadata_tag_scope_trap_returns_401(self) -> None:
        """Consumer scoped only for metadata tag public cannot access inventory route."""
        deck_path = hidden_scope_deck(SEED, Path("/tmp"))
        ingest_deck(deck_path)
        deck = yaml.safe_load(deck_path.read_text(encoding="utf-8"))
        route = deck["routes"][0]
        trap = next(c for c in deck["consumers"] if c["username"].startswith("tag-trap"))
        assert scope_allows(trap["jwt"]["scopes"], route["scope_tags"], route["tags"]) is False
        path = route["paths"][0]
        status, _, _ = proxy_request("GET", path, bearer=trap["jwt"]["key"])
        assert status == 401

    def test_valid_scope_on_hidden_route(self) -> None:
        """Procedural consumer key satisfies scope_tags on hidden route."""
        deck_path = hidden_scope_deck(SEED, Path("/tmp"))
        ingest_deck(deck_path)
        deck = yaml.safe_load(deck_path.read_text(encoding="utf-8"))
        route = deck["routes"][0]
        reader = next(c for c in deck["consumers"] if c["username"].startswith("reader"))
        path = route["paths"][0]
        status, _, _ = proxy_request("GET", path, bearer=reader["jwt"]["key"])
        assert status == 200

    def test_export_reflects_hidden_route_plugin_headers(self) -> None:
        """OpenAPI export after hidden ingest includes jwt-adjacent staged headers."""
        token = format(seed_offset(SEED, "export") % 10000, "04x")
        deck = {
            "services": [
                {
                    "name": f"exp-svc-{token}",
                    "url": "http://127.0.0.1:8000/upstream/exp",
                    "plugins": [
                        {
                            "name": "response-transformer",
                            "config": {"add": {"headers": ["X-Hidden-Service:yes"]}},
                        }
                    ],
                }
            ],
            "routes": [
                {
                    "name": f"exp-route-{token}",
                    "service": f"exp-svc-{token}",
                    "paths": [f"/api/export/{token}"],
                    "methods": ["GET"],
                    "plugins": [
                        {"name": "rate-limiting", "config": {"minute": 10}},
                        {
                            "name": "response-transformer",
                            "config": {"add": {"headers": ["X-Hidden-Route:yes"]}},
                        },
                    ],
                }
            ],
            "consumers": [],
        }
        deck_path = Path("/tmp") / f"export-deck-{token}.yaml"
        deck_path.write_text(yaml.safe_dump(deck), encoding="utf-8")
        ingest_deck(deck_path)
        status, spec = admin_get("/admin/export/openapi")
        assert status == 200
        export_path = f"/api/export/{token}"
        headers = spec["paths"][export_path]["get"]["responses"]["200"]["headers"]
        expected = staged_headers(deck["services"][0]["plugins"], deck["routes"][0]["plugins"])
        for name in expected:
            assert name in headers

    def test_rebuild_succeeds(self) -> None:
        proc = subprocess.run(["bash", str(APP / "scripts" / "verifier-rebuild.sh")], check=False)
        assert proc.returncode == 0
