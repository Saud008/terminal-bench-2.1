""" plugin merge precedence and access-phase chain order."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import yaml
from http_helpers import (
    ingest_deck,
    proxy_request,
    rebuild,
    reset_rates,
    start_daemon,
    stop_daemon,
)
from reference_chain import merge_plugins, run_chain

APP = Path("/app")
FIXTURES = APP / "fixtures"
CATALOG = json.loads((Path(__file__).parent / "catalog_m2.json").read_text(encoding="utf-8"))
SEED = os.environ.get("VERIFIER_SEED", CATALOG["seed"])


def seed_offset(seed: str, label: str) -> int:
    return int(hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()[:8], 16)


def per_run_api_key(seed: str) -> str:
    return f"key-{seed_offset(seed, 'api') & 0xFFFFFF:06x}"


class TestMilestone2:
    def setup_method(self) -> None:
        stop_daemon()
        rebuild()
        start_daemon()
        ingest_deck(FIXTURES / CATALOG["deck_fixture"])

    def teardown_method(self) -> None:
        stop_daemon()

    def test_service_and_route_transform_headers_merge(self) -> None:
        """Route-level transformer overlays service headers on catalog root GET."""
        reset_rates()
        status, hdrs, _ = proxy_request(
            "GET",
            CATALOG["rate_path"],
            api_key=per_run_api_key(SEED),
        )
        assert status == 200
        assert hdrs.get("X-Service-Layer") == "catalog"
        assert hdrs.get("X-Route-Layer") == "root-get"

    def test_rate_limit_blocks_before_response_transform(self) -> None:
        """429 responses must not include response-transformer headers."""
        reset_rates()
        api_key = per_run_api_key(SEED)
        path = CATALOG["rate_path"]
        limit = CATALOG["rate_limit"]
        last_status = 0
        last_hdrs: dict[str, str] = {}
        for _ in range(limit + 2):
            last_status, last_hdrs, _ = proxy_request("GET", path, api_key=api_key)
        assert last_status == 429
        assert "X-Route-Layer" not in last_hdrs

    def test_reference_chain_order_matches_runtime(self) -> None:
        """Independent chain simulator agrees with proxy header behavior."""
        deck = yaml.safe_load((FIXTURES / CATALOG["deck_fixture"]).read_text(encoding="utf-8"))
        svc = next(s for s in deck["services"] if s["name"] == "catalog-svc")
        rt = next(r for r in deck["routes"] if r["name"] == CATALOG["rate_route"])
        plugins = merge_plugins(svc.get("plugins") or [], rt.get("plugins") or [])
        counts: dict[str, int] = {}
        key = f"{CATALOG['rate_route']}:{per_run_api_key(SEED)}"
        blocked, headers, code = run_chain(
            plugins,
            rate_counts=counts,
            rate_key=key,
            limit=CATALOG["rate_limit"],
        )
        assert not blocked
        assert code == 200
        assert headers.get("X-Route-Layer") == "root-get"
        blocked, headers, code = run_chain(
            plugins,
            rate_counts=counts,
            rate_key=key,
            limit=CATALOG["rate_limit"],
        )
        while not blocked:
            blocked, headers, code = run_chain(
                plugins,
                rate_counts=counts,
                rate_key=key,
                limit=CATALOG["rate_limit"],
            )
        assert code == 429
        assert "X-Route-Layer" not in headers

    def test_per_run_api_key_isolates_rate_counters(self) -> None:
        """Different X-Api-Key values maintain separate rate buckets."""
        reset_rates()
        path = CATALOG["rate_path"]
        key_a = per_run_api_key(SEED)
        key_b = per_run_api_key(SEED + "-alt")
        limit = CATALOG["rate_limit"]
        for _ in range(limit + 1):
            proxy_request("GET", path, api_key=key_a)
        status_a, _, _ = proxy_request("GET", path, api_key=key_a)
        status_b, _, _ = proxy_request("GET", path, api_key=key_b)
        assert status_a == 429
        assert status_b == 200

    def test_rebuild_succeeds(self) -> None:
        proc = subprocess.run(["bash", str(APP / "scripts" / "verifier-rebuild.sh")], check=False)
        assert proc.returncode == 0
