"""compile-yard yard snapshot and loto ticket persistence.

Scenario ingest loads fixtures; verify-order report export writes JSON under /app/output/.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


class TestSublockCompileYard:
    def test_binary_present(self, relayctl_bin: Path):
        """CLI binary exists at the path declared in cli-surface.md."""
        assert relayctl_bin.is_file()

    def test_missing_subcommand_exits_nonzero(self, relayctl_bin: Path):
        """Invoking relayctl without a subcommand exits non-zero."""
        proc = subprocess.run(["/app/bin/relayctl"], capture_output=True, text=True, check=False)
        assert proc.returncode != 0

    def test_compile_emits_snapshot_and_loto_ticket(self, relayctl_bin: Path, seed_pool: list[str]):
        """compile-yard writes yard.snapshot and loto.ticket per bus-topology and lockout-tag docs."""
        seed = seed_pool[0]
        proc = subprocess.run(
            ["/app/bin/relayctl", "compile-yard", "--seed", seed, "--scenario", "basic-isolation"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        ticket = json.loads(Path("/app/var/sub/loto.ticket").read_text(encoding="utf-8"))
        assert snap["load_seq"] >= 1
        assert snap["scenario"] == "basic-isolation"
        assert "bus-src" in snap["buses"]
        assert ticket["ticket_id"].startswith("loto-")
        assert ticket["active"] is True

    def test_load_seq_monotonic_across_recompile(self, relayctl_bin: Path, seed_pool: list[str]):
        """Repeated compile-yard increments load_seq for cross-run persistence."""
        seed = seed_pool[2]
        subprocess.run(
            ["/app/bin/relayctl", "compile-yard", "--seed", seed, "--scenario", "basic-isolation"],
            check=True,
        )
        first = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))["load_seq"]
        subprocess.run(
            ["/app/bin/relayctl", "compile-yard", "--seed", seed, "--scenario", "energize-propagation"],
            check=True,
        )
        second = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))["load_seq"]
        assert second == first + 1

    def test_adjacency_pairs_sorted_lex(self, relayctl_bin: Path, seed_pool: list[str]):
        """yard.snapshot adjacency pairs are lex-sorted per bus-topology-schema.md."""
        subprocess.run(
            [
                "/app/bin/relayctl",
                "compile-yard",
                "--seed",
                seed_pool[1],
                "--scenario",
                "energize-propagation",
            ],
            check=True,
        )
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        for left, right in snap["adjacency"]:
            assert left <= right
