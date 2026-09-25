"""Behavioral verifier for gcrypt-filter smudge/clean/manifest repair."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from reference_gcrypt import (
    build_seed_plaintext,
    clean,
    encrypt_blob,
    export_manifest,
    filter_active,
    smudge,
)

APP = Path("/app")
CLI = APP / "bin" / "gcrypt-filter"
BASE_REPO = APP / "fixtures" / "repos" / "base"
SUB_REPO = APP / "fixtures" / "repos" / "submod-child"
CONFIG = APP / "config" / "filter.json"
MANIFEST_OUT = APP / "output" / "encrypted-manifest.json"
STAGING = APP / "state" / "staging"
SEED = os.environ.get("VERIFIER_SEED", "git-crypt-smudge-clean-filter-precedence-repair")


def _run(
    cmd: list[str],
    *,
    input_bytes: bytes | None = None,
    cwd: Path | None = None,
    text: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input_bytes,
        check=False,
        capture_output=True,
        text=text,
        cwd=str(cwd or APP),
    )


def reset_state() -> None:
    proc = _run(["bash", str(APP / "scripts" / "reset-state.sh")], text=True)
    assert proc.returncode == 0, _err(proc)


def _err(proc: subprocess.CompletedProcess) -> str:
    if isinstance(proc.stderr, bytes):
        return proc.stderr.decode("utf-8", errors="replace")
    return proc.stderr or ""


def run_clean(repo: Path, relpath: str, plaintext: bytes) -> subprocess.CompletedProcess:
    return _run(
        [str(CLI), "clean", "--repo", str(repo), "--path", relpath, "--config", str(CONFIG)],
        input_bytes=plaintext,
    )


def clean_blob(repo: Path, relpath: str, plaintext: bytes) -> bytes:
    """Run clean and return stdout; fail if the CLI did not succeed."""
    proc = run_clean(repo, relpath, plaintext)
    assert proc.returncode == 0, _err(proc)
    return proc.stdout


def run_smudge(
    repo: Path,
    relpath: str,
    blob: bytes,
    *,
    staging: bool = False,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    cmd = [str(CLI), "smudge", "--repo", str(repo), "--path", relpath, "--config", str(CONFIG)]
    if staging:
        cmd.append("--staging")
    return _run(cmd, input_bytes=blob, cwd=cwd)


def run_manifest(repo: Path, output: Path = MANIFEST_OUT) -> subprocess.CompletedProcess:
    return _run(
        [str(CLI), "export-manifest", "--repo", str(repo), "--output", str(output), "--config", str(CONFIG)],
    )


class TestCliGuards:
    """CLI validation and basic invocation."""

    def setup_method(self) -> None:
        reset_state()

    def test_missing_repo_exits_one(self) -> None:
        """clean must fail when --repo is not a directory."""
        proc = _run([str(CLI), "clean", "--repo", "/nope", "--path", "x.txt"], input_bytes=b"hi")
        assert proc.returncode == 1

    def test_missing_path_exits_one(self) -> None:
        """smudge must fail when --path is empty."""
        proc = _run([str(CLI), "smudge", "--repo", str(BASE_REPO), "--path", ""], input_bytes=b"hi")
        assert proc.returncode == 1


class TestCleanPassThrough:
    """Attribute check must precede encryption."""

    def setup_method(self) -> None:
        reset_state()

    def test_public_readme_clean_passthrough(self) -> None:
        """public/readme.txt must pass through clean without GCRYPT1 header."""
        raw = (BASE_REPO / "public/readme.txt").read_bytes()
        proc = run_clean(BASE_REPO, "public/readme.txt", raw)
        assert proc.returncode == 0, _err(proc)
        assert proc.stdout == raw
        assert not proc.stdout.startswith(b"GCRYPT1")

    def test_notes_txt_clean_passthrough(self) -> None:
        """notes.txt is explicitly -filter and must not be encrypted."""
        raw = (BASE_REPO / "notes.txt").read_bytes()
        proc = run_clean(BASE_REPO, "notes.txt", raw)
        assert proc.returncode == 0, _err(proc)
        assert proc.stdout == raw

    def test_secret_plain_encrypts(self) -> None:
        """secret/plain.txt must encrypt to reference blob."""
        raw = (BASE_REPO / "secret/plain.txt").read_bytes()
        proc = run_clean(BASE_REPO, "secret/plain.txt", raw)
        assert proc.returncode == 0, _err(proc)
        assert proc.stdout.decode("utf-8").startswith("GCRYPT1")
        assert proc.stdout == clean(BASE_REPO, "secret/plain.txt", raw)


class TestSmudgeRoundtrip:
    """Smudge decrypt and CRLF HMAC handling."""

    def setup_method(self) -> None:
        reset_state()

    def test_crlf_roundtrip(self) -> None:
        """CRLF plaintext must roundtrip after LF-normalized HMAC."""
        payload = b"line1\r\nline2\r\n"
        blob = clean(BASE_REPO, "secret/plain.txt", payload)
        proc = run_smudge(BASE_REPO, "secret/plain.txt", blob)
        assert proc.returncode == 0, _err(proc)
        assert proc.stdout == smudge(BASE_REPO, "secret/plain.txt", blob)

    def test_nested_data_bin_roundtrip(self) -> None:
        """secret/nested/data.bin encrypt/smudge must match reference."""
        raw = (BASE_REPO / "secret/nested/data.bin").read_bytes()
        blob = clean_blob(BASE_REPO, "secret/nested/data.bin", raw)
        proc = run_smudge(BASE_REPO, "secret/nested/data.bin", blob)
        assert proc.returncode == 0, _err(proc)
        assert proc.stdout == smudge(BASE_REPO, "secret/nested/data.bin", blob)

    def test_key_extension_encrypts(self) -> None:
        """vault/config.key must use *.key filter and roundtrip."""
        raw = (BASE_REPO / "vault/config.key").read_bytes()
        blob = clean_blob(BASE_REPO, "vault/config.key", raw)
        proc = run_smudge(BASE_REPO, "vault/config.key", blob)
        assert proc.returncode == 0, _err(proc)
        assert proc.stdout == smudge(BASE_REPO, "vault/config.key", blob)


class TestSubmoduleKeys:
    """Key resolution must use --repo root, not cwd."""

    def setup_method(self) -> None:
        reset_state()

    def test_smudge_from_subdirectory(self) -> None:
        """smudge run with cwd inside repo still resolves submodule key."""
        raw = (SUB_REPO / "secret/inner.txt").read_bytes()
        blob = clean(SUB_REPO, "secret/inner.txt", raw)
        subdir = SUB_REPO / "secret"
        proc = run_smudge(SUB_REPO, "secret/inner.txt", blob, cwd=subdir)
        assert proc.returncode == 0, _err(proc)
        assert proc.stdout == raw

    def test_child_key_id_in_blob(self) -> None:
        """submod-child uses feedface key id in encrypted blobs."""
        raw = (SUB_REPO / "overlay.key").read_bytes()
        proc = run_clean(SUB_REPO, "overlay.key", raw)
        assert proc.returncode == 0, _err(proc)
        assert b"KEY:feedface" in proc.stdout


class TestStagingRollback:
    """Failed decrypt must not leave staging artifacts."""

    def setup_method(self) -> None:
        reset_state()

    def test_bad_hmac_no_staging_file(self) -> None:
        """Corrupt HMAC must exit 2 and leave no staging file."""
        raw = (BASE_REPO / "secret/plain.txt").read_bytes()
        blob = encrypt_blob(BASE_REPO, raw)
        blob_bad = blob.replace(blob.splitlines()[-1], "HMAC:" + "0" * 64)
        rel = "secret/plain.txt"
        proc = run_smudge(BASE_REPO, rel, blob_bad.encode("utf-8"), staging=True)
        assert proc.returncode == 2
        assert not (STAGING / rel).exists()

    def test_success_staging_writes_file(self) -> None:
        """Successful smudge --staging writes decrypted bytes."""
        raw = (BASE_REPO / "secret/plain.txt").read_bytes()
        blob = clean_blob(BASE_REPO, "secret/plain.txt", raw)
        rel = "secret/plain.txt"
        proc = run_smudge(BASE_REPO, rel, blob, staging=True)
        assert proc.returncode == 0, _err(proc)
        staged = (STAGING / rel).read_bytes()
        assert staged == proc.stdout
        assert staged == smudge(BASE_REPO, rel, blob)


class TestExportManifest:
    """Manifest must respect attribute specificity."""

    def setup_method(self) -> None:
        reset_state()

    def test_base_manifest_matches_reference(self) -> None:
        """export-manifest for base repo must match independent reference."""
        proc = run_manifest(BASE_REPO)
        assert proc.returncode == 0, _err(proc)
        got = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        exp = export_manifest(BASE_REPO)
        assert got == exp

    def test_manifest_omits_public_and_notes(self) -> None:
        """Manifest must not list negated public/readme.txt or notes.txt."""
        proc = run_manifest(BASE_REPO)
        assert proc.returncode == 0, _err(proc)
        paths = {e["path"] for e in json.loads(MANIFEST_OUT.read_text())["entries"]}
        assert "public/readme.txt" not in paths
        assert "notes.txt" not in paths
        assert "secret/plain.txt" in paths
        assert "vault/config.key" in paths

    def test_submod_manifest_matches_reference(self) -> None:
        """submod-child manifest must match reference and omit public paths."""
        proc = run_manifest(SUB_REPO)
        assert proc.returncode == 0, _err(proc)
        got = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        assert got == export_manifest(SUB_REPO)
        paths = {e["path"] for e in got["entries"]}
        assert "public/note.txt" not in paths


class TestAntiCheat:
    """Hidden and seeded repos block hardcoded outputs."""

    def setup_method(self) -> None:
        reset_state()

    def test_seed_repo_negated_secret_public(self) -> None:
        """Generated seed repo keeps secret/public.txt plaintext on clean."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "seed-repo"
            gen = _run(
                ["bash", str(APP / "scripts" / "gen_repo_fixture.sh"), "--seed", SEED, "--output", str(root)],
            )
            assert gen.returncode == 0, _err(gen)
            raw = (root / "secret/public.txt").read_bytes()
            proc = run_clean(root, "secret/public.txt", raw)
            assert proc.returncode == 0, _err(proc)
            assert proc.stdout == raw
            assert not filter_active(root, "secret/public.txt")

    def test_seed_repo_overlay_encrypts(self) -> None:
        """Generated *.overlay path must encrypt per attributes."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "seed-repo"
            gen = _run(
                ["bash", str(APP / "scripts" / "gen_repo_fixture.sh"), "--seed", SEED, "--output", str(root)],
            )
            assert gen.returncode == 0, _err(gen)
            raw = (root / "vault.overlay").read_bytes()
            proc = run_clean(root, "vault.overlay", raw)
            assert proc.returncode == 0, _err(proc)
            assert proc.stdout == clean(root, "vault.overlay", raw)

    def test_seed_manifest_matches_reference(self) -> None:
        """Seed repo manifest must match Python reference."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "seed-repo"
            gen = _run(
                ["bash", str(APP / "scripts" / "gen_repo_fixture.sh"), "--seed", SEED, "--output", str(root)],
            )
            assert gen.returncode == 0, _err(gen)
            proc = run_manifest(root)
            assert proc.returncode == 0, _err(proc)
            got = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
            assert got == export_manifest(root)

    def test_non_catalog_payload_roundtrip(self) -> None:
        """Seeded plaintext not in bundled fixtures must roundtrip via reference."""
        payload = build_seed_plaintext(SEED)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "seed-repo"
            gen = _run(
                ["bash", str(APP / "scripts" / "gen_repo_fixture.sh"), "--seed", SEED, "--output", str(root)],
            )
            assert gen.returncode == 0, _err(gen)
            rel = "secret/seed.bin"
            blob = clean_blob(root, rel, payload)
            proc = run_smudge(root, rel, blob)
            assert proc.returncode == 0, _err(proc)
            assert proc.stdout == smudge(root, rel, blob)

    def test_tb3_repo_root_override(self) -> None:
        """TB3_REPO_ROOT hidden tree must clean/smudge per reference."""
        tb3 = os.environ.get("TB3_REPO_ROOT")
        assert tb3, "TB3_REPO_ROOT must be set by tests/test.sh"
        root = Path(tb3)
        assert root.is_dir(), f"TB3 fixture repo missing: {root}"
        rel = "secret/hidden.bin"
        payload = hashlib.sha256(f"tb3-{SEED}".encode()).digest()
        blob = clean_blob(root, rel, payload)
        proc = run_smudge(root, rel, blob)
        assert proc.returncode == 0, _err(proc)
        assert proc.stdout == smudge(root, rel, blob)
