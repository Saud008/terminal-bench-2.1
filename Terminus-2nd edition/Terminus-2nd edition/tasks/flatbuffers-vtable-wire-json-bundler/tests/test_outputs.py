"""Behavioral verifier for fbdecode JSON output (reference_flatc parity via flatc_parity_ecf23803)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest
from flatc_parity_ecf23803 import (
    _run_flatc_json,
    assert_scene_equal,
    build_buffer_bytes,
    hidden_absent_tags_scene,
    hidden_combo_trap_scene,
    hidden_deep_parent_chain_scene,
    hidden_tag_order_scene,
    normalize,
    procedural_scene,
    write_hidden_case,
    write_procedural_case,
    write_procedural_deep_nest,
    write_procedural_many_tags,
)
from wire_hash_helper import sha256_file

APP = Path("/app")
AGENT_SCHEMA = "/app/schema/scene.fbs"
SCHEMA = Path(AGENT_SCHEMA)
FIXTURES = APP / "fixtures" / "buffers"
STAGING_SNAPSHOT = APP / "state" / "decode.snapshot.json"
DECODE_LEDGER = APP / "state" / "decode.ledger.jsonl"
CLI = "fbdecode"
SEED = os.environ.get("VERIFIER_SEED", "fb-vtable-seed-7")
EXTRA_SEEDS = ("fb-matrix-13", "fb-matrix-42", "fb-matrix-88", "fb-matrix-101", "fb-matrix-204")

BUNDLED_CASES = (
    "shallow",
    "nested-chain",
    "tags-mixed",
    "struct-pad",
    "deep-nest",
    "many-tags",
    "metrics-defaults",
    "long-name-nest",
    "tags-order",
    "combo-nest-tags",
)


FAULT_SLOTS = {
    "ft26": "b00",
    "kx42": "b01",
    "ul82": "b02",
    "st38": "b03",
    "hn55": "b04",
    "cv20": "b05",
    "je67": "b06",
    "qg71": "b07",
    "yl49": "b08",
    "mp93": "b09",
    "rw14": "b10",
    "zq81": "b11",
}

REF_SLOTS = {
    "ft26": "r00",
    "kx42": "r01",
    "ul82": "r02",
    "st38": "r03",
    "hn55": "r04",
    "cv20": "r05",
    "je67": "r06",
    "qg71": "r07",
    "yl49": "r08",
    "mp93": "r09",
    "rw14": "r10",
    "zq81": "r11",
}

PATCH_TARGETS = {
    "kx42": APP / "src/kx42.rs",
    "ft26": APP / "src/ft26.rs",
    "st38": APP / "src/st38.rs",
    "ul82": APP / "src/ul82.rs",
    "hn55": APP / "src/hn55.rs",
    "cv20": APP / "src/cv20.rs",
    "je67": APP / "src/je67.rs",
    "qg71": APP / "src/qg71.rs",
    "yl49": APP / "src/yl49.rs",
    "mp93": APP / "src/mp93.rs",
    "rw14": APP / "src/rw14.rs",
    "zq81": APP / "src/zq81.rs",
}

BROKEN = Path("/opt/verifier-broken-fbdecode")
BROKEN_FALLBACK = Path(__file__).resolve().parent / "fault_lib"
REF_LIB = Path(__file__).resolve().parent / "verifier_ref_lib"

PROTECTED_SHA256: dict[str, str] = {
    "fixtures/buffers/deep-nest.bin": "7efbe23423f109e3deb534835ed215bad9bcbd6c9bb56c104c763bb5d42a9140",
    "fixtures/buffers/long-name-nest.bin": "ed375e68d380a38102a223518f24fcb51211d344dd601ba1fbca69dc5630eac7",
    "fixtures/buffers/many-tags.bin": "4821d8c721041ec4d6437fe92433346ac73ad7fed598389917436a6914cffd72",
    "fixtures/buffers/metrics-defaults.bin": "03635dd599f9097e14aad92726815c3020b014e86503d495de3b4d835846b4bb",
    "fixtures/buffers/nested-chain.bin": "81415c86c2595d3a501c7bf13f788fc393666e9af6b282a1e6e7dc010d667d81",
    "fixtures/buffers/shallow.bin": "e8f4964f01a701fae4678d2b874b4a1585622eb993cfa0ba00e7444a8158445c",
    "fixtures/buffers/struct-pad.bin": "35e1c5a17713a1bda4d065bc376590094f424032cd4091f897abb66f44b7c3b4",
    "fixtures/buffers/tags-mixed.bin": "7e2a6a08343e4f4123fec97edc5675baceffbbf7a87b1956fa3bb344b65cd128",
    "fixtures/buffers/tags-order.bin": "d513bd9429439c3de45bdd21794ad3fbcb791a986578d6f688a80cb2cac87c7d",
    "fixtures/buffers/combo-nest-tags.bin": "691ef74d199161b4aa0b8c23339c53a26bb9946b9d7d69eee8e10c205bc20df0",
    "fixtures/buffers/truncated.bin": "8c5b726477ef2f2aeb80c8330a4f8bc42c57d78e4af47d6eda3a7780a024b80c",
}


def _sha256(path: Path) -> str:
    return sha256_file(path)


def _is_sixteen_hex(value: str) -> bool:
    return len(value) == 16 and all(ch in "0123456789abcdef" for ch in value)


def _broken_root() -> Path:
    return BROKEN if BROKEN.is_dir() else BROKEN_FALLBACK


def _ref_lib_root() -> Path:
    assert REF_LIB.is_dir(), f"verifier ref lib missing: {REF_LIB}"
    return REF_LIB


@pytest.fixture(scope="session", autouse=True)
def verifier_prepare() -> None:
    """Reset state and rebuild fbdecode once before the pytest session."""
    reset_proc = subprocess.run(
        ["bash", str(APP / "scripts/reset-state.sh")],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )
    assert reset_proc.returncode == 0, reset_proc.stderr or reset_proc.stdout
    rebuild_proc = subprocess.run(
        ["bash", str(APP / "scripts/verifier-rebuild.sh")],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )
    assert rebuild_proc.returncode == 0, rebuild_proc.stderr or rebuild_proc.stdout


def _build_cli() -> None:
    for path in PATCH_TARGETS.values():
        os.utime(path, None)
    proc = subprocess.run(
        ["cargo", "build", "--locked", "--release", "-p", "fbpkg"],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    subprocess.run(
        ["install", "-m", "0755", str(APP / "target/release/fbdecode"), "/usr/local/bin/fbdecode"],
        check=True,
    )


def _decode(bin_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CLI, "decode", "--schema", AGENT_SCHEMA, "--input", f"{bin_path}"],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )


def _decode_json(bin_path: Path) -> dict:
    proc = _decode(bin_path)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _stage(bin_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CLI, "stage", "--schema", AGENT_SCHEMA, "--input", f"{bin_path}"],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )


def _export() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CLI, "export", "--schema", AGENT_SCHEMA],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )


def _verify() -> tuple[int, dict]:
    proc = subprocess.run(
        [CLI, "verify", "--schema", AGENT_SCHEMA],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )
    body = json.loads((proc.stdout or "{}").strip() or "{}")
    return proc.returncode, body


def _tamper_ledger_export_digest() -> None:
    lines = [
        line for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert lines, "decode ledger empty"
    entry = json.loads(lines[-1])
    entry["export_digest"] = "0" * 16
    lines[-1] = json.dumps(entry, separators=(",", ":"))
    DECODE_LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _stage_export_json(bin_path: Path) -> dict:
    stage_proc = _stage(bin_path)
    assert stage_proc.returncode == 0, stage_proc.stderr
    export_proc = _export()
    assert export_proc.returncode == 0, export_proc.stderr
    return json.loads(export_proc.stdout)


def _snapshot_sources() -> dict[str, str]:
    return {name: path.read_text(encoding="utf-8") for name, path in PATCH_TARGETS.items()}


def _restore_sources(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        PATCH_TARGETS[name].write_text(content, encoding="utf-8")
        os.utime(PATCH_TARGETS[name], None)


def _restore_broken_sources() -> None:
    root = _broken_root()
    for name, dest in PATCH_TARGETS.items():
        shutil.copyfile(root / f"{FAULT_SLOTS[name]}.rs", dest)
        os.utime(dest, None)


def _ref_patch_path(name: str) -> Path:
    root = _ref_lib_root()
    slot = REF_SLOTS[name]
    path = root / f"{slot}.rs"
    if path.is_file():
        return path
    raise FileNotFoundError(f"verifier reference patch missing for {name}")


def _install_patch(name: str) -> None:
    dest = PATCH_TARGETS[name]
    shutil.copyfile(_ref_patch_path(name), dest)
    os.utime(dest, None)


def assert_mismatch_or_invalid(
    proc: subprocess.CompletedProcess[str],
    expected: dict,
    *,
    bin_path: Path | None = None,
) -> None:
    if proc.returncode != 0:
        return
    got = json.loads(proc.stdout)
    if normalize(got) != normalize(expected):
        return
    raise AssertionError(f"broken decoder matched reference for {bin_path or 'buffer'}")


@contextmanager
def _patched_modules(*names: str):
    saved = _snapshot_sources()
    try:
        _restore_broken_sources()
        for name in names:
            _install_patch(name)
        _build_cli()
        yield
    finally:
        _restore_sources(saved)
        _build_cli()


@contextmanager
def _patched_module(name: str):
    with _patched_modules(name):
        yield


class TestFbDecode:
    def setup_method(self) -> None:
        _build_cli()

    def test_tecf238_fixture_integrity(self) -> None:
        """Bundled buffers must remain unchanged."""
        for rel, digest in PROTECTED_SHA256.items():
            assert _sha256(APP / rel) == digest, rel

    def test_tecf238_fbdecode_cli_requires_schema_and_input(self) -> None:
        """CLI must reject invocations without required flags."""
        proc = subprocess.run(
            [CLI, "decode", "--input", str(FIXTURES / "shallow.bin")],
            cwd=APP,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2

    @pytest.mark.parametrize("name", BUNDLED_CASES)
    def test_tecf238_fixturebuf_matches_flatc(self, name: str) -> None:
        """Decoder output must match flatc reference JSON."""
        buf = FIXTURES / f"{name}.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)

    def test_tecf238_nested_parent_chain_depth(self) -> None:
        """Nested-chain fixture must surface three entity levels."""
        buf = FIXTURES / "nested-chain.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)
        parent = got["root"].get("parent")
        assert parent and parent.get("parent")

    def test_tecf238_deep_nest_four_levels(self) -> None:
        """Deep-nest fixture must surface four entity levels."""
        buf = FIXTURES / "deep-nest.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)
        depth = 0
        level = got["root"]
        while level is not None:
            depth += 1
            level = level.get("parent")
        assert depth == 4

    def test_tecf238_absent_tags_not_empty_list(self) -> None:
        """Missing tags field on parent entity must not become an empty vector."""
        buf = FIXTURES / "tags-mixed.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)
        parent = got["root"]["parent"]
        assert "tags" not in parent or parent.get("tags") is None

    def test_tecf238_many_tags_vector_stride(self) -> None:
        """Many-tags fixture requires correct per-element vector stride."""
        buf = FIXTURES / "many-tags.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)
        assert len(got["root"]["tags"]) == len(expected["root"]["tags"])

    def test_tecf238_struct_padding_coordinates(self) -> None:
        """Long name fixture requires aligned inline Vec3 reads."""
        buf = FIXTURES / "struct-pad.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)

    def test_tecf238_long_name_nest_parent_position(self) -> None:
        """Nested parent with a long name still requires aligned Vec3 reads."""
        buf = FIXTURES / "long-name-nest.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)

    def test_tecf238_tag_vector_preserves_wire_order(self) -> None:
        """Tag vectors must keep flatc element order, not alphabetical key order."""
        buf = FIXTURES / "tags-order.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)
        assert [tag["key"] for tag in got["root"]["tags"]] == [
            tag["key"] for tag in expected["root"]["tags"]
        ]

    def test_tecf238_combo_nest_tags_matches_flatc(self) -> None:
        """Combined nest, padding, tags, and metrics must match flatc."""
        buf = FIXTURES / "combo-nest-tags.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)

    def test_tecf238_combo_nest_parent_chain_and_metrics(self) -> None:
        """Combo fixture must surface nested parents, padded Vec3, and metrics."""
        buf = FIXTURES / "combo-nest-tags.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)
        assert got["root"].get("metrics") is not None
        assert got["root"].get("parent") is not None

    def test_tecf238_metrics_defaults_flag_count(self) -> None:
        """Absent metrics.flag_count must decode as the schema default."""
        buf = FIXTURES / "metrics-defaults.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)

    def test_tecf238_truncated_buffer_errors(self) -> None:
        """Truncated buffers must fail decode."""
        proc = _decode(FIXTURES / "truncated.bin")
        assert proc.returncode == 1
        assert proc.stdout.strip() == ""

    def test_tecf238_decode_writes_wiresnap_wsnap(self) -> None:
        """Successful decode must persist /app/state/decode.snapshot.json on disk"""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        buf = FIXTURES / "shallow.bin"
        proc = _decode(buf)
        assert proc.returncode == 0, proc.stderr
        assert str(STAGING_SNAPSHOT) == "/app/state/decode.snapshot.json"
        assert STAGING_SNAPSHOT.is_file(), "/app/state/decode.snapshot.json missing"
        envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
        assert isinstance(envelope.get("hn55"), str) and envelope["hn55"]
        assert isinstance(envelope.get("scene"), dict)
        expected = _run_flatc_json(buf)
        assert_scene_equal(envelope["scene"], expected)

    def test_tecf238_stage_appends_decode_decodejournal(self) -> None:
        """Stage must append a line to /app/state/decode.ledger.jsonl bound to staging."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        stage_proc = _stage(FIXTURES / "shallow.bin")
        assert stage_proc.returncode == 0, stage_proc.stderr
        assert str(DECODE_LEDGER) == "/app/state/decode.ledger.jsonl"
        assert DECODE_LEDGER.is_file(), "/app/state/decode.ledger.jsonl missing"
        lines = [
            line
            for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(lines) == 1
        entry = json.loads(lines[0])
        envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
        assert entry["hn55"] == envelope["hn55"]
        assert entry["revision"] == envelope["scene"]["revision"]
        assert _is_sixteen_hex(entry["hn55"])
        assert isinstance(entry.get("export_digest"), str) and entry["export_digest"]
        assert _is_sixteen_hex(entry["export_digest"])
        assert ":" not in entry["export_digest"]

    def test_tecf238_decodejournal_wdigests_bind_each_rewiresnap(self) -> None:
        """Every ledger line must carry sixteen-hex digests matching its staging envelope."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        for name in ("shallow", "tags-order", "combo-nest-tags"):
            assert _stage(FIXTURES / f"{name}.bin").returncode == 0
            envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
            lines = [
                line
                for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            head = json.loads(lines[-1])
            assert head["hn55"] == envelope["hn55"]
            assert _is_sixteen_hex(head["hn55"])
            assert _is_sixteen_hex(head["export_digest"])
            assert ":" not in head["export_digest"]

    def test_tecf238_trapbuf_synthscene_decodejournal_wdigest_chain(self) -> None:
        """Procedural restaging must keep ledger digests aligned with staging envelopes."""
        with tempfile.TemporaryDirectory() as tmp:
            first_bin, _ = write_procedural_case(Path(tmp), "fb-matrix-88")
            second_bin, _ = write_procedural_many_tags(Path(tmp), "fb-matrix-101")
            subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
            assert _stage(first_bin).returncode == 0
            assert _stage(second_bin).returncode == 0
            lines = [
                line
                for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            assert len(lines) == 2
            for entry_line in lines:
                entry = json.loads(entry_line)
                assert _is_sixteen_hex(entry["hn55"])
                assert _is_sixteen_hex(entry["export_digest"])
                assert ":" not in entry["export_digest"]
            envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
            head = json.loads(lines[-1])
            assert head["hn55"] == envelope["hn55"]
            export_proc = _export()
            assert export_proc.returncode == 0, export_proc.stderr

    def test_tecf238_jsonout_without_stage_fails(self) -> None:
        """Export must fail when no staging snapshot or ledger exists."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        proc = _export()
        assert proc.returncode == 1
        assert proc.stdout.strip() == ""

    def test_tecf238_stage_then_jsonout_matches_decode(self) -> None:
        """Split stage/export must match combined decode output."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        buf = FIXTURES / "tags-order.bin"
        expected = _run_flatc_json(buf)
        got = _stage_export_json(buf)
        assert_scene_equal(got, expected)

    def test_tecf238_rewiresnap_replaces_wsnap_and_head(self) -> None:
        """A second stage on a different buffer must replace snapshot and ledger head."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        first = FIXTURES / "shallow.bin"
        second = FIXTURES / "tags-order.bin"
        assert _stage(first).returncode == 0
        first_envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
        assert _stage(second).returncode == 0
        second_envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
        assert first_envelope["hn55"] != second_envelope["hn55"]
        assert second_envelope["scene"]["root"]["name"] != first_envelope["scene"]["root"]["name"]
        lines = [
            line
            for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(lines) == 2
        head = json.loads(lines[-1])
        assert head["hn55"] == second_envelope["hn55"]
        assert head["revision"] == second_envelope["scene"]["revision"]
        expected = _run_flatc_json(second)
        got = json.loads(_export().stdout)
        assert_scene_equal(got, expected)

    def test_tecf238_decode_after_prior_stage_uses_latest_input(self) -> None:
        """Combined decode after an earlier stage must bind to the new input only."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        assert _stage(FIXTURES / "metrics-defaults.bin").returncode == 0
        buf = FIXTURES / "combo-nest-tags.bin"
        expected = _run_flatc_json(buf)
        got = _decode_json(buf)
        assert_scene_equal(got, expected)
        envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
        assert_scene_equal(envelope["scene"], expected)

    def test_tecf238_decodejournal_seq_monotonic_on_rewiresnap(self) -> None:
        """Ledger seq must increment on every successful stage."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        for idx, name in enumerate(("shallow", "nested-chain", "many-tags"), start=1):
            assert _stage(FIXTURES / f"{name}.bin").returncode == 0
            lines = [
                line
                for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            assert len(lines) == idx
            assert json.loads(lines[-1])["seq"] == idx

    def test_tecf238_aligncheck_after_stage_reports_aligned(self) -> None:
        """verify must report aligned staging and ledger after stage."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        assert _stage(FIXTURES / "shallow.bin").returncode == 0
        code, body = _verify()
        assert code == 0
        assert body.get("aligned") is True

    def test_tecf238_aligncheck_fails_tampered_decodejournal_jsonout_wdigest(self) -> None:
        """verify must report misalignment when ledger export_digest was tampered."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        assert _stage(FIXTURES / "shallow.bin").returncode == 0
        _tamper_ledger_export_digest()
        code, body = _verify()
        assert code == 1
        assert body.get("aligned") is False

    def test_tecf238_jsonout_fails_tampered_decodejournal_jsonout_wdigest(self) -> None:
        """export must reject a ledger whose export_digest no longer matches staging."""
        subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
        assert _stage(FIXTURES / "shallow.bin").returncode == 0
        _tamper_ledger_export_digest()
        proc = _export()
        assert proc.returncode != 0

    def test_tecf238_trapbuf_absent_tags_stage_jsonout_path(self) -> None:
        """Export subcommand must omit absent tag fields from staged scenes."""
        with tempfile.TemporaryDirectory() as tmp:
            scene = hidden_absent_tags_scene()
            bin_path = write_hidden_case(Path(tmp), scene, "hidden-absent-tags-stage.bin")
            subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
            expected = _run_flatc_json(bin_path)
            got = _stage_export_json(bin_path)
            assert_scene_equal(got, expected)
            assert "tags" not in got["root"]
            assert "tags" not in got["root"]["parent"]

    def test_tecf238_synthscene_seed_buffer(self) -> None:
        """Seed-derived scene built with flatc must decode identically."""
        scene = procedural_scene(SEED)
        bin_path = Path("/tmp/procedural-scene.bin")
        bin_path.write_bytes(build_buffer_bytes(scene))
        expected = _run_flatc_json(bin_path)
        got = _decode_json(bin_path)
        assert_scene_equal(got, expected)

    @pytest.mark.parametrize("seed", EXTRA_SEEDS)
    def test_tecf238_synthscene_matrix_scene(self, seed: str) -> None:
        """Independent seeds must decode procedural scenes identically."""
        with tempfile.TemporaryDirectory() as tmp:
            bin_path, _ = write_procedural_case(Path(tmp), seed)
            expected = _run_flatc_json(bin_path)
            got = _decode_json(bin_path)
            assert_scene_equal(got, expected)

    @pytest.mark.parametrize("seed", EXTRA_SEEDS)
    def test_tecf238_synthscene_matrix_deep_nest(self, seed: str) -> None:
        """Independent seeds must decode procedural deep-nest chains."""
        with tempfile.TemporaryDirectory() as tmp:
            bin_path, scene = write_procedural_deep_nest(Path(tmp), seed)
            expected = _run_flatc_json(bin_path)
            got = _decode_json(bin_path)
            assert_scene_equal(got, expected)
            depth = 0
            level = scene["root"]
            while level is not None:
                depth += 1
                level = level.get("parent")
            assert depth >= 3

    @pytest.mark.parametrize("seed", EXTRA_SEEDS)
    def test_tecf238_synthscene_matrix_many_tags(self, seed: str) -> None:
        """Independent seeds must decode procedural multi-tag vectors."""
        with tempfile.TemporaryDirectory() as tmp:
            bin_path, scene = write_procedural_many_tags(Path(tmp), seed)
            expected = _run_flatc_json(bin_path)
            got = _decode_json(bin_path)
            assert_scene_equal(got, expected)
            assert len(scene["root"]["tags"]) >= 3

    def test_tecf238_trapbuf_absent_tags_omit_json_field(self) -> None:
        """Verifier-only buffer: absent tags must omit the JSON field entirely (/opt/verifier-fixtures)."""
        with tempfile.TemporaryDirectory() as tmp:
            scene = hidden_absent_tags_scene()
            bin_path = write_hidden_case(Path(tmp), scene, "hidden-absent-tags.bin")
            expected = _run_flatc_json(bin_path)
            assert "tags" not in expected["root"]
            assert "tags" not in expected["root"]["parent"]
            got = _decode_json(bin_path)
            assert_scene_equal(got, expected)
            assert "tags" not in got["root"]
            assert "tags" not in got["root"]["parent"]

    def test_tecf238_trapbuf_tag_order_preserves_wire_sequence(self) -> None:
        """Verifier-only buffer: tag vectors must not be reordered for export."""
        with tempfile.TemporaryDirectory() as tmp:
            bin_path = write_hidden_case(
                Path(tmp), hidden_tag_order_scene(), "hidden-tag-order.bin"
            )
            expected = _run_flatc_json(bin_path)
            got = _decode_json(bin_path)
            assert_scene_equal(got, expected)
            keys = [tag["key"] for tag in got["root"]["tags"]]
            assert keys == ["zebra", "alpha", "middle"]

    def test_tecf238_trapbuf_deep_parent_chain_matches_flatc(self) -> None:
        """Verifier-only buffer: four-level parent chains require correct indirection."""
        with tempfile.TemporaryDirectory() as tmp:
            bin_path = write_hidden_case(
                Path(tmp), hidden_deep_parent_chain_scene(), "hidden-deep-parent.bin"
            )
            expected = _run_flatc_json(bin_path)
            got = _decode_json(bin_path)
            assert_scene_equal(got, expected)
            depth = 0
            level = got["root"]
            while level is not None:
                depth += 1
                level = level.get("parent")
            assert depth == 4

    def test_tecf238_trapbuf_combo_trap_matches_flatc(self) -> None:
        """Hidden combo trap must preserve nested absent tags (/opt/verifier partial-patch probes)."""
        with tempfile.TemporaryDirectory() as tmp:
            bin_path = write_hidden_case(
                Path(tmp), hidden_combo_trap_scene(), "hidden-combo-trap.bin"
            )
            expected = _run_flatc_json(bin_path)
            got = _decode_json(bin_path)
            assert_scene_equal(got, expected)
            parent = got["root"]["parent"]
            assert "tags" not in parent or parent.get("tags") is None
            assert got["root"]["tags"] == expected["root"]["tags"]
            assert got["root"]["parent"]["position"] == expected["root"]["parent"]["position"]
            assert (
                got["root"]["parent"]["parent"]["tags"]
                == expected["root"]["parent"]["parent"]["tags"]
            )

    @pytest.mark.parametrize(
        "module",
        [
            "kx42",
            "ft26",
            "st38",
            "ul82",
            "hn55",
            "cv20",
            "je67",
            "qg71",
            "yl49",
            "mp93",
            "rw14",
            "zq81",
        ],
    )
    def test_tecf238_partial_fix_still_fails_fixturebuf(self, module: str) -> None:
        """Fixing only one decoder module must not satisfy all bundled fixtures."""
        with _patched_module(module):
            mismatches = 0
            for name in BUNDLED_CASES:
                buf = FIXTURES / f"{name}.bin"
                proc = _decode(buf)
                if proc.returncode != 0:
                    mismatches += 1
                    continue
                expected = _run_flatc_json(buf)
                got = json.loads(proc.stdout)
                if normalize(got) != normalize(expected):
                    mismatches += 1
            assert mismatches > 0, f"partial {module} patch matched every bundled fixture"

    def test_tecf238_partial_fault_fb_wire_fails_shallow(self) -> None:
        """Golden wire alone must not decode shallow.bin correctly."""
        with _patched_module("kx42"):
            buf = FIXTURES / "shallow.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_fault_fb_vtable_fails_shallow(self) -> None:
        """Golden vtable alone must not decode shallow.bin correctly."""
        with _patched_module("ft26"):
            buf = FIXTURES / "shallow.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_fault_fb_table_fails_struct_pad(self) -> None:
        """Golden table alone must not decode struct-pad.bin correctly."""
        with _patched_module("st38"):
            buf = FIXTURES / "struct-pad.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_fault_fb_table_fails_nested_chain(self) -> None:
        """Golden table alone must not decode nested-chain.bin correctly."""
        with _patched_module("st38"):
            buf = FIXTURES / "nested-chain.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_fault_fb_vector_fails_tags_mixed(self) -> None:
        """Golden vector alone must not decode tags-mixed.bin correctly."""
        with _patched_module("ul82"):
            buf = FIXTURES / "tags-mixed.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_fault_fb_vector_fails_many_tags(self) -> None:
        """Golden vector alone must not decode many-tags.bin correctly."""
        with _patched_module("ul82"):
            buf = FIXTURES / "many-tags.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_fault_fb_jsonout_fails_tags_order(self) -> None:
        """Golden legacy export alone must not fix stdout when export_stage still reorders tags."""
        with _patched_module("je67"):
            buf = FIXTURES / "tags-order.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_fault_fb_jsonout_stage_fails_tags_order(self) -> None:
        """Golden export_stage alone must not preserve tag vector wire order."""
        with _patched_module("qg71"):
            buf = FIXTURES / "tags-order.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_fault_fb_wiresnap_fails_tags_mixed(self) -> None:
        """Golden staging alone must not synthesize empty tag lists for absent fields."""
        with _patched_module("cv20"):
            buf = FIXTURES / "tags-mixed.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_fault_fb_wiresnap_fails_shallow(self) -> None:
        """Golden staging alone must not repair wire decode errors."""
        with _patched_module("cv20"):
            buf = FIXTURES / "shallow.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_vtable_table_still_fails_tags_order(self) -> None:
        """Golden vtable and table without vector/export still mis-order tag vectors."""
        with _patched_modules("ft26", "st38"):
            buf = FIXTURES / "tags-order.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_vtable_vector_still_fails_nested_chain(self) -> None:
        """Golden vtable and vector without st38.rs still break parent indirection."""
        with _patched_modules("ft26", "ul82"):
            buf = FIXTURES / "nested-chain.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_table_vector_still_fails_shallow(self) -> None:
        """Golden table and vector without vst38.rs still mis-resolve vtables."""
        with _patched_modules("st38", "ul82"):
            buf = FIXTURES / "shallow.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_vtable_table_vector_still_fails_tags_order(self) -> None:
        """Fixing decode modules without staging and export still reorders tag vectors."""
        with _patched_modules("ft26", "st38", "ul82"):
            buf = FIXTURES / "tags-order.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_vtable_table_vector_jsonout_still_fails_trapbuf_absent_tags(self) -> None:
        """Wire and legacy export fixes without staging still synthesize absent tag fields."""
        with (
            _patched_modules("kx42", "ft26", "st38", "ul82", "je67"),
            tempfile.TemporaryDirectory() as tmp,
        ):
            bin_path = write_hidden_case(
                Path(tmp), hidden_absent_tags_scene(), "hidden-absent-tags.bin"
            )
            expected = _run_flatc_json(bin_path)
            proc = _decode(bin_path)
            assert_mismatch_or_invalid(proc, expected, bin_path=bin_path)

    def test_tecf238_partial_vtable_table_vector_wiresnap_still_fails_tags_order(self) -> None:
        """Wire and staging fixes without export_stage still reorder tag vectors."""
        with _patched_modules("kx42", "ft26", "st38", "ul82", "cv20"):
            buf = FIXTURES / "tags-order.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_oracle_fb_vector_only_still_fails_trapbuf_absent_tags(self) -> None:
        """Golden vector alone must not synthesize empty tag lists for absent fields."""
        with _patched_module("ul82"), tempfile.TemporaryDirectory() as tmp:
            bin_path = write_hidden_case(
                Path(tmp), hidden_absent_tags_scene(), "hidden-absent-tags.bin"
            )
            expected = _run_flatc_json(bin_path)
            proc = _decode(bin_path)
            assert_mismatch_or_invalid(proc, expected, bin_path=bin_path)

    def test_tecf238_partial_oracle_fb_jsonout_only_still_fails_trapbuf_tag_order(self) -> None:
        """Golden legacy export alone must not reorder hidden tag vectors via export_stage."""
        with _patched_module("je67"), tempfile.TemporaryDirectory() as tmp:
            bin_path = write_hidden_case(
                Path(tmp), hidden_tag_order_scene(), "hidden-tag-order.bin"
            )
            expected = _run_flatc_json(bin_path)
            proc = _decode(bin_path)
            assert_mismatch_or_invalid(proc, expected, bin_path=bin_path)

    def test_tecf238_partial_oracle_fb_jsonout_stage_only_still_fails_trapbuf_combo_trap(self) -> None:
        """Golden export_stage alone must not satisfy hidden combo trap."""
        with _patched_module("qg71"), tempfile.TemporaryDirectory() as tmp:
            bin_path = write_hidden_case(
                Path(tmp), hidden_combo_trap_scene(), "hidden-combo-trap.bin"
            )
            expected = _run_flatc_json(bin_path)
            proc = _decode(bin_path)
            assert_mismatch_or_invalid(proc, expected, bin_path=bin_path)

    def test_tecf238_partial_oracle_fb_wiresnap_only_still_fails_trapbuf_absent_tags(self) -> None:
        """Golden staging alone must not omit synthesized empty tag lists."""
        with _patched_module("cv20"), tempfile.TemporaryDirectory() as tmp:
            bin_path = write_hidden_case(
                Path(tmp), hidden_absent_tags_scene(), "hidden-absent-tags.bin"
            )
            expected = _run_flatc_json(bin_path)
            proc = _decode(bin_path)
            assert_mismatch_or_invalid(proc, expected, bin_path=bin_path)

    def test_tecf238_partial_oracle_fb_vtable_table_still_fails_trapbuf_deep_parent(self) -> None:
        """Golden vtable and table without vector/staging/export still break hidden parent chains."""
        with (
            _patched_modules("ft26", "st38"),
            tempfile.TemporaryDirectory() as tmp,
        ):
            bin_path = write_hidden_case(
                Path(tmp), hidden_deep_parent_chain_scene(), "hidden-deep-parent.bin"
            )
            expected = _run_flatc_json(bin_path)
            proc = _decode(bin_path)
            assert_mismatch_or_invalid(proc, expected, bin_path=bin_path)

    def test_tecf238_partial_vtable_only_still_fails_trapbuf_combo_trap(self) -> None:
        """Golden vtable alone must not satisfy hidden combo trap."""
        with _patched_module("ft26"), tempfile.TemporaryDirectory() as tmp:
            bin_path = write_hidden_case(
                Path(tmp), hidden_combo_trap_scene(), "hidden-combo-trap.bin"
            )
            expected = _run_flatc_json(bin_path)
            proc = _decode(bin_path)
            assert_mismatch_or_invalid(proc, expected, bin_path=bin_path)

    def test_tecf238_partial_oracle_fb_all_but_decodejournal_still_writes_broken_wdigest(self) -> None:
        """Golden wire path without ledger must still persist broken ledger digests."""
        with _patched_modules(
            "kx42",
            "ft26",
            "st38",
            "ul82",
            "hn55",
            "cv20",
            "je67",
            "qg71",
            "rw14",
        ):
            subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
            with tempfile.TemporaryDirectory() as tmp:
                bin_path = write_hidden_case(
                    Path(tmp), hidden_combo_trap_scene(), "hidden-combo-trap.bin"
                )
                proc = _decode(bin_path)
                assert proc.returncode == 0, proc.stderr
                lines = [
                    line
                    for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                assert len(lines) == 1
                entry = json.loads(lines[0])
                assert not _is_sixteen_hex(entry["export_digest"])
                envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
                assert _is_sixteen_hex(envelope["hn55"])

    def test_tecf238_partial_oracle_fb_modules_still_fail_jsonout_with_broken_decodejournal(self) -> None:
        """Wire through runner fixes without ledger must leave invalid ledger heads."""
        with _patched_modules(
            "kx42",
            "ft26",
            "st38",
            "ul82",
            "hn55",
            "cv20",
            "je67",
            "qg71",
            "rw14",
            "zq81",
        ):
            subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
            buf = FIXTURES / "shallow.bin"
            stage_proc = _stage(buf)
            assert stage_proc.returncode == 0, stage_proc.stderr
            lines = [
                line
                for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            assert len(lines) == 1
            entry = json.loads(lines[0])
            assert not _is_sixteen_hex(entry["export_digest"])
            envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
            assert _is_sixteen_hex(envelope["hn55"])

    def test_tecf238_partial_oracle_fb_wiresnap_jsonout_still_writes_broken_decodejournal_on_rewiresnap(
        self,
    ) -> None:
        """Staging and export_stage fixes without ledger must leave broken ledger heads on restage."""
        with _patched_modules(
            "kx42",
            "ft26",
            "st38",
            "ul82",
            "hn55",
            "cv20",
            "je67",
            "qg71",
            "rw14",
            "zq81",
        ):
            subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
            assert _stage(FIXTURES / "shallow.bin").returncode == 0
            assert _stage(FIXTURES / "tags-order.bin").returncode == 0
            lines = [
                line
                for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            assert len(lines) == 2
            head = json.loads(lines[-1])
            assert head["seq"] == 2
            assert not _is_sixteen_hex(head["export_digest"])
            envelope = json.loads(STAGING_SNAPSHOT.read_text(encoding="utf-8"))
            assert head["hn55"] == envelope["hn55"]
            assert _is_sixteen_hex(envelope["hn55"])
            assert not _is_sixteen_hex(head["export_digest"])
            export_proc = _export()
            assert export_proc.returncode == 0, export_proc.stderr

    def test_tecf238_partial_oracle_fb_runner_still_needs_jsonout_stage(self) -> None:
        """Golden wire path without runner must still route stdout through the legacy export decoy."""
        with _patched_modules(
            "kx42",
            "ft26",
            "st38",
            "ul82",
            "hn55",
            "cv20",
            "qg71",
            "mp93",
            "yl49",
            "zq81",
        ):
            buf = FIXTURES / "tags-order.bin"
            proc = _decode(buf)
            expected = _run_flatc_json(buf)
            assert_mismatch_or_invalid(proc, expected, bin_path=buf)

    def test_tecf238_partial_oracle_fb_guard_only_allows_tampered_decodejournal(self) -> None:
        """Golden modules except guard must export after ledger export_digest tampering."""
        with _patched_modules(
            "kx42",
            "ft26",
            "st38",
            "ul82",
            "hn55",
            "cv20",
            "je67",
            "qg71",
            "mp93",
            "yl49",
            "rw14",
        ):
            subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
            assert _stage(FIXTURES / "shallow.bin").returncode == 0
            _tamper_ledger_export_digest()
            proc = _export()
            assert proc.returncode == 0, proc.stderr + proc.stdout

    def test_tecf238_partial_oracle_fb_decodejournal_wdigest_only_still_fails_sixteen_hex(self) -> None:
        """Golden ledger append without ledger_digest must persist non-conforming export digests."""
        with _patched_modules(
            "kx42",
            "ft26",
            "st38",
            "ul82",
            "hn55",
            "cv20",
            "je67",
            "qg71",
            "mp93",
            "rw14",
            "zq81",
        ):
            subprocess.run(["bash", str(APP / "scripts/reset-state.sh")], check=True, cwd=APP)
            assert _stage(FIXTURES / "shallow.bin").returncode == 0
            lines = [
                line
                for line in DECODE_LEDGER.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            entry = json.loads(lines[-1])
            assert not _is_sixteen_hex(entry["export_digest"])

    def test_tecf238_partial_oracle_fb_wire_wdigest_only_still_fails_wiresnap_reload(self) -> None:
        """Golden wire_digest alone cannot satisfy bundled decode without wire modules."""
        with _patched_module("hn55"):
            proc = _decode(FIXTURES / "shallow.bin")
            expected = _run_flatc_json(FIXTURES / "shallow.bin")
            assert_mismatch_or_invalid(proc, expected, bin_path=FIXTURES / "shallow.bin")
