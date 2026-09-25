""" declarative ingest atomicity and route matching."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import yaml

from http_helpers import ingest_deck, proxy_request, rebuild, start_daemon, stop_daemon
from reference_matcher import hidden_deck_path, per_run_api_key, reference_match, seed_offset

APP = Path("/app")
FIXTURES = APP / "fixtures"
CATALOG = json.loads((Path(__file__).parent / "catalog_m1.json").read_text(encoding="utf-8"))
SEED = os.environ.get("VERIFIER_SEED", CATALOG["seed"])


def bundled_routes() -> list[dict]:
    deck = yaml.safe_load((FIXTURES / CATALOG["match_fixture"]).read_text(encoding="utf-8"))
    return deck["routes"]


class TestMilestone1:
    def setup_method(self) -> None:
        stop_daemon()
        rebuild()
        start_daemon()

    def teardown_method(self) -> None:
        stop_daemon()

    def test_invalid_plugin_ingest_is_atomic(self) -> None:
        """Unknown plugin rejects entire deck without persisting routes."""
        path = FIXTURES / CATALOG["ingest_invalid_fixture"]
        status, body = ingest_deck(path)
        assert status == 422
        assert body.get("ok") is False
        assert body.get("routes_loaded", -1) == 0

    def test_method_specificity_returns_404_not_405(self) -> None:
        """GET on POST-only longer prefix yields 404 when no GET route exists."""
        ingest_deck(FIXTURES / CATALOG["match_fixture"])
        status, _, _ = proxy_request(CATALOG["method_trap_verb"], CATALOG["method_trap_path"])
        assert status == 404

    def test_longest_path_with_matching_method(self) -> None:
        """Among GET routes, the longest matching path prefix wins."""
        token = format(seed_offset(SEED, "longest") % 10000, "04x")
        deck = {
            "services": [
                {
                    "name": f"svc-{token}",
                    "url": "http://127.0.0.1:8000/upstream/match",
                    "plugins": [],
                }
            ],
            "routes": [
                {
                    "name": f"root-{token}",
                    "service": f"svc-{token}",
                    "paths": [f"/api/m/{token}"],
                    "methods": ["GET"],
                    "plugins": [],
                },
                {
                    "name": f"leaf-{token}",
                    "service": f"svc-{token}",
                    "paths": [f"/api/m/{token}/items"],
                    "methods": ["GET"],
                    "plugins": [],
                },
            ],
            "consumers": [],
        }
        deck_path = Path("/tmp") / f"match-deck-{token}.yaml"
        deck_path.write_text(yaml.safe_dump(deck), encoding="utf-8")
        ingest_deck(deck_path)
        leaf_path = f"/api/m/{token}/items"
        status, hdrs, _ = proxy_request("GET", leaf_path, api_key=per_run_api_key(SEED))
        assert status == 200
        assert hdrs.get("X-Matched-Route") == f"leaf-{token}"

    def test_hidden_deck_method_matrix(self) -> None:
        """Procedural hidden routes enforce method-aware matching."""
        deck_path = hidden_deck_path(SEED, Path("/tmp"))
        ingest_deck(deck_path)
        deck = yaml.safe_load(deck_path.read_text(encoding="utf-8"))
        routes = deck["routes"]
        get_path = next(r["paths"][0] for r in routes if r["methods"] == ["GET"])
        post_path = next(r["paths"][0] for r in routes if r["methods"] == ["POST"])
        assert get_path == post_path
        assert reference_match(routes, "GET", get_path) != reference_match(routes, "POST", post_path)
        assert proxy_request("GET", get_path)[0] == 200
        assert proxy_request("POST", post_path)[0] == 200
        post_only_path = f"{get_path}/submit"
        assert proxy_request("GET", post_only_path)[0] == 404

    def test_rebuild_succeeds(self) -> None:
        proc = subprocess.run(["bash", str(APP / "scripts" / "verifier-rebuild.sh")], check=False)
        assert proc.returncode == 0
