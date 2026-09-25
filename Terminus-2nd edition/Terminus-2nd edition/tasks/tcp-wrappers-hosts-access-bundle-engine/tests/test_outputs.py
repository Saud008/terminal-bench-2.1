"""Behavioral verifier for hostsctl TCP wrapper merge and decide."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_decide import bundle_fingerprint, decide, merge_rules, publish_seal, seeded_last_octet

APP = Path("/app")
BUNDLES = APP / "fixtures/bundles"
OUTPUT = APP / "output"
CATALOG = APP / "fixtures/catalog.json"
CLI = Path("/usr/local/bin/hostsctl")
RESET = APP / "scripts/reset-state.sh"
INGEST = APP / "scripts/ingest.sh"
BROKEN_LIB = Path(__file__).resolve().parent / "broken_lib"
LIB = APP / "lib"
SEED = os.environ.get("VERIFIER_SEED", "tcp-wrappers-hosts-access-bundle-engine")
TB3_BUNDLES = Path("/opt/verifier-fixtures/tb3-bundles")


def restore_broken_lib() -> None:
    """Reset /app/lib to the shipped broken modules (for partial-fix traps)."""
    for src in BROKEN_LIB.glob("*.sh"):
        install_partial_script(src, LIB / src.name)


def install_partial_script(src: Path, dest: Path) -> None:
    """Copy a partial-trap script with Unix line endings."""
    data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.write_bytes(data)


def snapshot_lib() -> dict[str, str]:
    return {str(p): p.read_text(encoding="utf-8") for p in sorted(LIB.glob("*.sh"))}


def restore_lib_snapshot(saved: dict[str, str]) -> None:
    for path, content in saved.items():
        Path(path).write_text(content, encoding="utf-8")

MERGE_BUNDLES = [
    "office-edge",
    "dmz-ipv6",
    "lab-aliases",
    "except-trap",
    "merge-order",
    "wrap-join",
]

DECIDE_CASES = [
    ("office-edge", "sshd", "203.0.113.10"),
    ("office-edge", "sshd", "198.51.100.99"),
    ("office-edge", "sshd", "198.51.100.50"),
    ("merge-order", "sshd", "192.0.2.55"),
    ("except-trap", "sshd", "192.0.2.66"),
    ("except-trap", "sshd", "192.0.2.67"),
    ("except-trap", "sshd", "192.0.2.65"),
    ("lab-aliases", "secure-shell", "10.20.5.1"),
    ("dmz-ipv6", "sshd", "2001:db8:1000:1::5"),
    ("dmz-ipv6", "sshd", "2001:db8:ffff:1::1"),
    ("wrap-join", "sshd", "198.51.100.50"),
]

PROTECTED_REL = [
    "bundles/office-edge/manifest.json",
    "bundles/office-edge/allow/10-sshd-subnet.allow",
    "bundles/office-edge/allow/20-vpn-except.allow",
    "bundles/office-edge/deny/10-scanners.deny",
    "bundles/office-edge/deny/20-blocked-host.deny",
    "bundles/dmz-ipv6/manifest.json",
    "bundles/dmz-ipv6/allow/10-front.allow",
    "bundles/dmz-ipv6/deny/10-lab-segment.deny",
    "bundles/lab-aliases/manifest.json",
    "bundles/lab-aliases/daemon-aliases.json",
    "bundles/lab-aliases/allow/10-shell.allow",
    "bundles/lab-aliases/deny/10-guest.deny",
    "bundles/except-trap/manifest.json",
    "bundles/except-trap/allow/10-wide.allow",
    "bundles/merge-order/manifest.json",
    "bundles/merge-order/allow/05-host.allow",
    "bundles/merge-order/allow/10-net.allow",
    "bundles/merge-order/deny/10-default.deny",
    "bundles/wrap-join/manifest.json",
    "bundles/wrap-join/allow/10-wrap.allow",
    "catalog.json",
    "seeds.json",
    "sessions/office-edge-sample.json",
]

EXPECTED_SHA256 = {
    "bundles/office-edge/manifest.json": "b1ea5a69bb4e75877ffa4099a230a13bd4c2a562c12e5d80e0419709dd64a791",
    "bundles/office-edge/allow/10-sshd-subnet.allow": "9a34f0588a8cf495397be5a6fc3ab3591d1cb455248253a71b48e0822357fc18",
    "bundles/office-edge/allow/20-vpn-except.allow": "25651fd24cc73562f237d2be271a810c3a7ef7d1cfcedfd348f3a19537f12ef5",
    "bundles/office-edge/deny/10-scanners.deny": "df74fc4c1f9d3f1b4527286ad16941e84af1026c3da53586e9cdab20b96e5ab3",
    "bundles/office-edge/deny/20-blocked-host.deny": "8af0c1e476ddfc465a66a74aac3ca898e3701e59263bb5fc93bd9b39a94a99c2",
    "bundles/dmz-ipv6/manifest.json": "8a5cdbef63b590088b79211f0315dd1ab83fd5c3d28d4856a8f30d18c09c7d49",
    "bundles/dmz-ipv6/allow/10-front.allow": "18be07c2a022ce0923149b151eb77369d74d0ff40d23b81b478a32ee3eb44a79",
    "bundles/dmz-ipv6/deny/10-lab-segment.deny": "e6830867ad835fef8cd5d7df7d0fc17263534b8ef9ac92b4200c818f540e5349",
    "bundles/lab-aliases/manifest.json": "9e534a532d1b7b55a7a7a5bee703bf613416e80eeff2ba2269574ed3fd199e1c",
    "bundles/lab-aliases/daemon-aliases.json": "056ca9902d4020b94b3fed07de7aecac8b52c351ffd190d27b8fc065e0dd6087",
    "bundles/lab-aliases/allow/10-shell.allow": "02dcaa026170cdbdedac9baf343489fe9b4eb271652f6a4c78945c73ea63e2cd",
    "bundles/lab-aliases/deny/10-guest.deny": "627849496c53ad7b89a233486ea415937656e856daf06e936e378fbf81897e71",
    "bundles/except-trap/manifest.json": "f22bd4842ace43661c9961061d5b394650305dfd43ea9bfa2a460f38d9314df4",
    "bundles/except-trap/allow/10-wide.allow": "15ddd0fd9dae8e9f0eaf442f0b370ef3106a8d8cf8e6c5687cbe9ba26f8c4620",
    "bundles/merge-order/manifest.json": "44d5d2ed4d80b82a57178e3e6c5a0f08ceface2b44158c064cedc4d7614c17e6",
    "bundles/merge-order/allow/05-host.allow": "7be1269eea9ed3ab03c7ab41c398021f5bdef81b47b1276d56298be60472a4c2",
    "bundles/merge-order/allow/10-net.allow": "9749bc61644b49bcc84394af017a3213f9040487b85b161f739075a7bffc8de8",
    "bundles/merge-order/deny/10-default.deny": "1b8ed0ca7d49858d6a479baee99fd92fcdc85cabb9351d917c12d0ff85783d24",
    "bundles/wrap-join/manifest.json": "8bce687140224ffa4c1df0f2a139f85d8ee21acacd739995b6b61c6e919f2704",
    "bundles/wrap-join/allow/10-wrap.allow": "4d39476a6d2f2a9797b487849e1805b21cb34b12d99ce67712e2c0766798551d",
    "catalog.json": "7ff4236f86ffd4364cd9941b609bbc2ac2d1c4ace3394ab1bf7ebd3b111f50d7",
    "seeds.json": "d3894b2a4c09d417f66a3566424b3b58477d309ac6a9479356049da9ae08cbcc",
    "sessions/office-edge-sample.json": "b79935f813a5963b7fc2ce6ac8d6b1a873c121fc624a2d0eeaa27de36fff98d5",
}


def dynamic_manifest() -> dict:
    path = APP / "fixtures/_dynamic_manifest.json"
    assert path.is_file(), "missing build-time dynamic manifest"
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def bundle_path(bundle: str) -> str:
    p = Path(bundle)
    if p.is_absolute() or bundle.startswith("/"):
        return str(p)
    return str(BUNDLES / bundle)


def merge_cli(bundle: str, export: Path) -> subprocess.CompletedProcess[str]:
    export.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            str(CLI),
            "merge",
            "--bundle",
            bundle_path(bundle),
            "--export",
            str(export),
        ]
    )


def decide_cli(
    bundle: str, daemon: str, ip: str, export: Path
) -> subprocess.CompletedProcess[str]:
    export.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            str(CLI),
            "decide",
            "--bundle",
            bundle_path(bundle),
            "--daemon",
            daemon,
            "--ip",
            ip,
            "--export",
            str(export),
        ]
    )


class TestHostsctlTcpWrappers:
    """hostsctl merge/decide requirements."""

    def setup_method(self) -> None:
        reset()

    def test_hostsctl_installed(self) -> None:
        """CLI must be on PATH and executable without installing packages."""
        assert CLI.is_file()
        assert INGEST.is_file()
        proc = run(["hostsctl"])
        assert proc.returncode == 2
        assert "hostsctl merge" in (proc.stdout or proc.stderr)

    def test_fixture_integrity(self) -> None:
        """Bundled manifests and fragments must remain unmodified."""
        for rel in PROTECTED_REL:
            path = APP / "fixtures" / rel
            assert path.is_file(), rel
            assert sha256_file(path) == EXPECTED_SHA256[rel], rel
        on_disk = json.loads(CATALOG.read_text(encoding="utf-8"))
        assert on_disk["bundles"] == [
            "office-edge",
            "dmz-ipv6",
            "lab-aliases",
            "except-trap",
            "merge-order",
            "wrap-join",
        ]

    @pytest.mark.parametrize("bundle", MERGE_BUNDLES)
    def test_merge_matches_reference(self, bundle: str) -> None:
        """Every catalog bundle merge export must match the reference engine."""
        out = OUTPUT / f"merge-{bundle}.json"
        proc = merge_cli(bundle, out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = merge_rules(BUNDLES / bundle)
        assert got == want

    @pytest.mark.parametrize("bundle", MERGE_BUNDLES)
    def test_merge_stats_match_reference(self, bundle: str) -> None:
        """Merge stats and rule ordering must match the reference merge export."""
        out = OUTPUT / f"merge-stats-{bundle}.json"
        proc = merge_cli(bundle, out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = merge_rules(BUNDLES / bundle)
        assert got["stats"] == want["stats"]
        if want["stats"]["allow_rules"] > 0 and want["stats"]["deny_rules"] > 0:
            assert got["rules"][0]["side"] == "allow", (
                f"{bundle}: merged rules must list allow before deny"
            )

    @pytest.mark.parametrize(
        "bundle,daemon,ip",
        DECIDE_CASES,
        ids=[f"{b}-{ip}" for b, _, ip in DECIDE_CASES],
    )
    def test_decide_matches_reference(self, bundle: str, daemon: str, ip: str) -> None:
        """Decide exports must follow allow-then-deny evaluation and canonical daemons."""
        out = OUTPUT / f"decide-{bundle}-{ip.replace(':', '_')}.json"
        proc = decide_cli(bundle, daemon, ip, out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = decide(BUNDLES / bundle, daemon, ip)
        assert got == want

    def test_merge_allow_rules_precede_deny_in_export(self) -> None:
        """Merged rules must list every allow rule before any deny rule."""
        out = OUTPUT / "merge-order-check.json"
        proc = merge_cli("merge-order", out)
        assert proc.returncode == 0
        rules = json.loads(out.read_text(encoding="utf-8"))["rules"]
        seen_deny = False
        for rule in rules:
            if rule["side"] == "deny":
                seen_deny = True
            if seen_deny and rule["side"] == "allow":
                pytest.fail("allow rule appeared after deny rule in merged export")

    def test_partial_stale_cache_fingerprint_still_fails(self) -> None:
        """Using cache without fingerprint validation must diverge after fp tamper."""
        partial = Path(__file__).resolve().parent / "broken_lib/common.sh"
        saved = snapshot_lib()
        try:
            restore_broken_lib()
            install_partial_script(partial, LIB / "common.sh")
            merge_cli("office-edge", OUTPUT / "partial-cache-merge.json")
            cache_path = APP / "work/merged/office-edge.json"
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            cache["fingerprint"] = "0" * 64
            cache_path.write_text(json.dumps(cache) + "\n", encoding="utf-8")
            out = OUTPUT / "partial-cache-decide.json"
            proc = decide_cli("office-edge", "sshd", "198.51.100.99", out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            want = decide(BUNDLES / "office-edge", "sshd", "198.51.100.99")
            assert got != want
        finally:
            restore_lib_snapshot(saved)

    def test_partial_decide_all_deny_skip_still_fails(self) -> None:
        """Allow-then-deny with ALL-only deny rows skipped must not pass scanner net case."""
        partial = Path(__file__).resolve().parent / "broken_decide_partial.sh"
        saved = snapshot_lib()
        try:
            restore_broken_lib()
            install_partial_script(partial, LIB / "decide.sh")
            out = OUTPUT / "partial-decide-scanner.json"
            proc = decide_cli("office-edge", "sshd", "198.51.100.99", out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            want = decide(BUNDLES / "office-edge", "sshd", "198.51.100.99")
            assert got != want
            assert got["decision"] == "deny"
            assert got["matched_rule_index"] == -1
            assert got["reason"] == "default_deny"
        finally:
            restore_lib_snapshot(saved)

    def test_partial_merge_order_without_stats_still_fails(self) -> None:
        """Correct allow/deny ordering with wrong stats must fail reference merge."""
        partial = Path(__file__).resolve().parent / "broken_merge_partial.sh"
        saved = snapshot_lib()
        try:
            restore_broken_lib()
            install_partial_script(partial, LIB / "merge.sh")
            out = OUTPUT / "partial-merge-stats.json"
            proc = merge_cli("merge-order", out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            want = merge_rules(BUNDLES / "merge-order")
            assert got["rules"] == want["rules"]
            assert got["stats"]["allow_rules"] != want["stats"]["allow_rules"]
            assert got["stats"]["deny_rules"] != want["stats"]["deny_rules"]
            assert got != want
        finally:
            restore_lib_snapshot(saved)

    def test_partial_wrong_rule_index_still_fails(self) -> None:
        """Deny-first cached indices without decide renumbering must fail reference export."""
        saved = snapshot_lib()
        try:
            restore_broken_lib()
            reset()
            merge_cli("office-edge", OUTPUT / "partial-index-merge.json")
            out = OUTPUT / "partial-index.json"
            proc = decide_cli("office-edge", "sshd", "198.51.100.50", out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            want = decide(BUNDLES / "office-edge", "sshd", "198.51.100.50")
            assert got["decision"] == want["decision"]
            assert got != want
        finally:
            restore_lib_snapshot(saved)

    def test_partial_merge_stats_still_fails_wrap_join(self) -> None:
        """Correct wrap-join rule export with swapped stats must fail reference merge."""
        partial = Path(__file__).resolve().parent / "broken_merge_partial.sh"
        saved = snapshot_lib()
        try:
            restore_broken_lib()
            install_partial_script(partial, LIB / "merge.sh")
            out = OUTPUT / "partial-wrap-merge.json"
            proc = merge_cli("wrap-join", out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            want = merge_rules(BUNDLES / "wrap-join")
            assert got["rules"] == want["rules"]
            assert got["stats"] != want["stats"]
            assert got != want
        finally:
            restore_lib_snapshot(saved)

    def test_merge_writes_fingerprinted_cache(self) -> None:
        """Merge must persist cache with fragment-sensitive fingerprint and publish seal."""
        out = OUTPUT / "merge-cache-check.json"
        proc = merge_cli("office-edge", out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        cache_path = APP / "work/merged/office-edge.json"
        staging_path = APP / "work/staging/office-edge.json"
        assert cache_path.is_file()
        assert staging_path.is_file()
        merged = json.loads(out.read_text(encoding="utf-8"))
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        staging = json.loads(staging_path.read_text(encoding="utf-8"))
        assert cache["fingerprint"] == bundle_fingerprint(BUNDLES / "office-edge")
        assert cache["publish_seal"] == publish_seal(merged)
        assert staging["publish_seal"] == publish_seal(merged)
        assert cache["merged"] == merged

    def test_merge_staging_seal_binds_rule_order(self) -> None:
        """Publish seal must change when allow/deny order changes."""
        out = OUTPUT / "merge-order-staging.json"
        proc = merge_cli("merge-order", out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        merged = json.loads(out.read_text(encoding="utf-8"))
        seal = publish_seal(merged)
        sides = [r["side"] for r in merged["rules"]]
        assert sides.index("deny") > sides.index("allow")
        stats_only = hashlib.sha256(
            json.dumps(merged["stats"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        assert seal != stats_only

    def test_partial_publish_stats_seal_still_fails(self) -> None:
        """Correct merge export with stats-only publish seal must fail cache contract."""
        golden_merge = Path(__file__).resolve().parent / "golden_merge_partial.sh"
        partial = Path(__file__).resolve().parent / "broken_lib/publish.sh"
        saved = snapshot_lib()
        try:
            restore_broken_lib()
            install_partial_script(golden_merge, LIB / "merge.sh")
            install_partial_script(partial, LIB / "publish.sh")
            out = OUTPUT / "partial-publish-merge.json"
            proc = merge_cli("office-edge", out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            merged = json.loads(out.read_text(encoding="utf-8"))
            want = merge_rules(BUNDLES / "office-edge")
            assert merged == want
            cache = json.loads((APP / "work/merged/office-edge.json").read_text(encoding="utf-8"))
            assert cache.get("publish_seal") != publish_seal(merged)
        finally:
            restore_lib_snapshot(saved)

    def test_decide_refreshes_stale_publish_seal(self) -> None:
        """Decide must rebuild when cache publish seal no longer matches merged order."""
        merge_cli("office-edge", OUTPUT / "merge-stale-seal.json")
        cache_path = APP / "work/merged/office-edge.json"
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        cache["publish_seal"] = "0" * 64
        cache_path.write_text(json.dumps(cache) + "\n", encoding="utf-8")
        out = OUTPUT / "decide-stale-seal.json"
        proc = decide_cli("office-edge", "sshd", "198.51.100.99", out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = decide(BUNDLES / "office-edge", "sshd", "198.51.100.99")
        assert got == want
        refreshed = json.loads(cache_path.read_text(encoding="utf-8"))
        merged = refreshed["merged"]
        assert refreshed["publish_seal"] == publish_seal(merged)

    def test_decide_refreshes_stale_cache_fingerprint(self) -> None:
        """Decide must rebuild when cache fingerprint no longer matches bundle bytes."""
        merge_cli("office-edge", OUTPUT / "merge-stale-fp.json")
        cache_path = APP / "work/merged/office-edge.json"
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        cache["fingerprint"] = "0" * 64
        cache_path.write_text(json.dumps(cache) + "\n", encoding="utf-8")
        out = OUTPUT / "decide-stale-fp.json"
        proc = decide_cli("office-edge", "sshd", "198.51.100.99", out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = decide(BUNDLES / "office-edge", "sshd", "198.51.100.99")
        assert got == want
        refreshed = json.loads(cache_path.read_text(encoding="utf-8"))
        assert refreshed["fingerprint"] == bundle_fingerprint(BUNDLES / "office-edge")

    def test_replay_session_matches_fresh_decide(self) -> None:
        """Replay must flag tuples that diverge from fresh decide evaluation."""
        merge_cli("office-edge", OUTPUT / "merge-replay-prep.json")
        session = APP / "fixtures/sessions/office-edge-sample.json"
        entries = json.loads(session.read_text(encoding="utf-8"))
        for entry in entries:
            probe = OUTPUT / f"replay-probe-{entry['ip'].replace(':', '_')}.json"
            proc = decide_cli("office-edge", entry["daemon"], entry["ip"], probe)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(probe.read_text(encoding="utf-8"))
            assert got["decision"] == entry["decision"]
            assert got["matched_rule_index"] == entry["matched_rule_index"]
        out = OUTPUT / "replay-good.json"
        proc = run(
            [
                str(CLI),
                "replay",
                "--bundle",
                str(BUNDLES / "office-edge"),
                "--session",
                str(session),
                "--export",
                str(out),
            ]
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["mismatches"] == []

    def test_seed_dynamic_decide_office_edge(self) -> None:
        """Seed-derived client IP must follow reference allow-then-deny semantics."""
        seeds = json.loads((APP / "fixtures/seeds.json").read_text(encoding="utf-8"))
        tag = hashlib.sha256(SEED.encode()).hexdigest()[:6]
        ip = seeded_last_octet(seeds["base_ipv4"], SEED, seeds["probe_slot"])
        out = OUTPUT / f"seed-decide-{tag}.json"
        proc = decide_cli("office-edge", seeds["probe_daemon"], ip, out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = decide(BUNDLES / "office-edge", seeds["probe_daemon"], ip)
        assert got == want

    def test_partial_cidr_only_still_fails_scanner_deny(self) -> None:
        """IPv4/EXCEPT fixes alone must not restore ALL deny matching for scanner net."""
        partial = Path(__file__).resolve().parent / "broken_cidr_partial.sh"
        saved = snapshot_lib()
        try:
            restore_broken_lib()
            install_partial_script(partial, LIB / "cidr.sh")
            out = OUTPUT / "partial-cidr-scanner.json"
            proc = decide_cli("office-edge", "sshd", "198.51.100.99", out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            want = decide(BUNDLES / "office-edge", "sshd", "198.51.100.99")
            assert got != want
            assert got["matched_rule_index"] == -1
            assert want["matched_rule_index"] == 2
        finally:
            restore_lib_snapshot(saved)

    def test_except_trap_second_host_requires_multi_except(self) -> None:
        """Second ALL EXCEPT host must not match when only the first host is excluded."""
        out = OUTPUT / "except-trap-second-host.json"
        proc = decide_cli("except-trap", "sshd", "192.0.2.67", out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = decide(BUNDLES / "except-trap", "sshd", "192.0.2.67")
        assert got == want
        assert got["decision"] == "deny"
        assert got["reason"] == "default_deny"

    def test_dynamic_except_bundle_matches_reference(self) -> None:
        """Seed-derived dynamic bundle must honor full multi-host ALL EXCEPT semantics."""
        meta = dynamic_manifest()
        bundle = meta["dynamic_bundle"]
        probe = meta["probe_allow"]
        out = OUTPUT / "dynamic-except-decide.json"
        proc = decide_cli(bundle, "sshd", probe, out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = decide(BUNDLES / bundle, "sshd", probe)
        assert got == want
        assert got["decision"] == "allow"

    def test_dynamic_except_bundle_rejects_second_host(self) -> None:
        """Dynamic bundle must exclude every listed EXCEPT host, not just the first."""
        meta = dynamic_manifest()
        bundle = meta["dynamic_bundle"]
        blocked = meta["except_hosts"][1]
        out = OUTPUT / "dynamic-except-blocked.json"
        proc = decide_cli(bundle, "sshd", blocked, out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = decide(BUNDLES / bundle, "sshd", blocked)
        assert got == want
        assert got["decision"] == "deny"

    def test_except_trap_multi_host_all_except_reference(self) -> None:
        """except-trap ALL EXCEPT must match reference for every listed host and allow probes."""
        cases = [
            ("192.0.2.65", "allow"),
            ("192.0.2.66", "deny"),
            ("192.0.2.67", "deny"),
        ]
        for ip, decision in cases:
            out = OUTPUT / f"except-multi-{ip.replace('.', '-')}.json"
            proc = decide_cli("except-trap", "sshd", ip, out)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(out.read_text(encoding="utf-8"))
            want = decide(BUNDLES / "except-trap", "sshd", ip)
            assert got == want
            assert got["decision"] == decision

    def test_replay_broken_stub_hides_mismatches(self) -> None:
        """Replay must flag divergent rows; broken stub incorrectly reports success."""
        merge_cli("office-edge", OUTPUT / "merge-replay-broken.json")
        bad_session = OUTPUT / "bad-session.json"
        bad_session.write_text(
            json.dumps(
                [
                    {
                        "daemon": "sshd",
                        "ip": "198.51.100.50",
                        "decision": "allow",
                        "matched_rule_index": 0,
                    }
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        out = OUTPUT / "replay-fixed.json"
        proc = run(
            [
                str(CLI),
                "replay",
                "--bundle",
                str(BUNDLES / "office-edge"),
                "--session",
                str(bad_session),
                "--export",
                str(out),
            ]
        )
        assert proc.returncode == 1, proc.stderr or proc.stdout
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["mismatches"]

        saved = snapshot_lib()
        try:
            restore_broken_lib()
            broken_out = OUTPUT / "replay-broken-lib.json"
            proc_broken = run(
                [
                    str(CLI),
                    "replay",
                    "--bundle",
                    str(BUNDLES / "office-edge"),
                    "--session",
                    str(bad_session),
                    "--export",
                    str(broken_out),
                ]
            )
            assert proc_broken.returncode == 0
            broken_payload = json.loads(broken_out.read_text(encoding="utf-8"))
            assert broken_payload["mismatches"] == []
        finally:
            restore_lib_snapshot(saved)

    @pytest.mark.skipif(not TB3_BUNDLES.is_dir(), reason="TB3 bundles only in image")
    def test_tb3_scanner_sweep_hidden_decide(self) -> None:
        """TB3 bundle must match reference ALL deny on scanner net."""
        bundle = TB3_BUNDLES / "tb3-scanner-sweep"
        out = OUTPUT / "tb3-scanner-sweep.json"
        proc = decide_cli(str(bundle), "sshd", "198.51.100.99", out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = decide(bundle, "sshd", "198.51.100.99")
        assert got == want
        assert got["decision"] == "deny"
        assert got["matched_rule_index"] == 1

    @pytest.mark.skipif(not TB3_BUNDLES.is_dir(), reason="TB3 bundles only in image")
    def test_tb3_dual_except_hidden_decide(self) -> None:
        """TB3 ALL EXCEPT must deny every listed excluded host, not only the first."""
        bundle = TB3_BUNDLES / "tb3-dual-except"
        out = OUTPUT / "tb3-dual-except.json"
        proc = decide_cli(str(bundle), "sshd", "192.0.2.66", out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        want = decide(bundle, "sshd", "192.0.2.66")
        assert got == want
        assert got["decision"] == "deny"
        assert got["reason"] == "default_deny"
