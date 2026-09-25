"""Verifier for cmake-fetchcontent-manifest-audit (single-step)."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
LIB = APP / "lib"
BIN = APP / "bin" / "cmake-audit"
PROJECT = APP / "project"
VENDOR = APP / "vendor-cache"
PINS = PROJECT / "overlays" / "pinned.cmake"
INSTALL = APP / "install"
TESTS = Path(__file__).resolve().parent
GOLDEN_LIB = TESTS / "golden_lib"
BROKEN_LIB = TESTS / "broken_lib"
GOLDEN_BIN = TESTS / "golden_bin" / "cmake-audit"


def _run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        text=True,
        cwd=str(APP),
    )


def reset_state() -> None:
    _run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def install_text(src: Path, dest: Path) -> None:
    data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    if dest.suffix == ".sh" or dest.name == "cmake-audit":
        dest.chmod(dest.stat().st_mode | 0o111)


def snapshot_lib() -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in sorted(LIB.glob("*.sh")):
        out[str(p)] = p.read_bytes()
    out[str(BIN)] = BIN.read_bytes()
    return out


def restore_snapshot(saved: dict[str, bytes]) -> None:
    for path, content in saved.items():
        Path(path).write_bytes(content)


@pytest.fixture(autouse=True)
def _isolate_modules() -> None:
    saved = snapshot_lib()
    yield
    restore_snapshot(saved)


def join_rel(base: str, rel: str) -> str:
    if rel.startswith("/"):
        rel = rel.lstrip("/")
    parts: list[str] = []
    for p in f"{base}/{rel}".replace("\\", "/").split("/"):
        if p in ("", "."):
            continue
        if p == "..":
            if parts:
                parts.pop()
            continue
        parts.append(p)
    return "/".join(parts)


def parse_list_file(root: Path, rel: str) -> dict:
    abs_path = root / rel
    list_dir = str(abs_path.parent.resolve())
    includes_raw: list[str] = []
    subdirs_raw: list[str] = []
    text_lines = []
    for line in abs_path.read_text(encoding="utf-8").splitlines():
        if "#" in line:
            line = line.split("#", 1)[0]
        text_lines.append(line)
        m_inc = re.search(r'include\s*\(\s*"([^"]+)"', line)
        if m_inc:
            includes_raw.append(join_rel(str(Path(rel).parent), m_inc.group(1)))
        m_sub = re.search(r'add_subdirectory\s*\(\s*"?([^"\s()]+)', line)
        if m_sub:
            subdirs_raw.append(join_rel(str(Path(rel).parent), m_sub.group(1).strip('"')))
    blob = "\n".join(text_lines)
    fetch: list[dict] = []
    for m in re.finditer(
        r"(?is)FetchContent_Declare\s*\(\s*([^\s()]+)\s*(.*?)(?=FetchContent_Declare\s*\(|\Z)",
        blob,
    ):
        name = m.group(1).strip()
        body = m.group(2)
        url_m = re.search(r"URL\s+file://[^\s)]+/([^\s)/]+\.tar\.gz)", body)
        hash_m = re.search(r"URL_HASH\s+SHA256=([0-9a-fA-F]+)", body)
        fetch.append(
            {
                "name": name,
                "url": url_m.group(1) if url_m else "",
                "url_hash": hash_m.group(1).lower() if hash_m else "",
            }
        )
    return {
        "path": rel.replace("\\", "/"),
        "list_dir": list_dir,
        "includes_raw": includes_raw,
        "subdirs_raw": subdirs_raw,
        "fetchcontent": fetch,
    }


def reference_ingest(root: Path) -> dict:
    root = root.resolve()
    queue = ["CMakeLists.txt"]
    visited: set[str] = set()
    files: list[dict] = []
    while queue:
        rel = queue.pop(0)
        if rel in visited:
            continue
        visited.add(rel)
        if not (root / rel).is_file():
            continue
        rec = parse_list_file(root, rel)
        files.append(rec)
        for sub in sorted(set(rec["subdirs_raw"])):
            queue.append(f"{sub}/CMakeLists.txt")
    return {"version": 1, "root": str(root), "files": files}


def reference_tree(ingest: dict) -> dict:
    files = []
    for rec in ingest["files"]:
        files.append(
            {
                "path": rec["path"],
                "list_dir": rec["list_dir"],
                "includes": sorted(set(rec["includes_raw"])),
                "subdirs": sorted(set(rec["subdirs_raw"])),
                "fetchcontent": list(rec["fetchcontent"]),
            }
        )
    files.sort(key=lambda r: r["path"])
    return {"root": ingest["root"], "files": files}


def reference_hash(tree: dict, vendor: Path, pins_text: str) -> tuple[dict, dict]:
    pin_map = {
        m.group(1).lower(): m.group(2)
        for m in re.finditer(
            r'set\s*\(\s*PIN_(.+?)_GIT_COMMIT\s+"([^"]+)"\s*\)',
            pins_text,
            flags=re.IGNORECASE,
        )
    }
    deps_by_name: dict[str, dict] = {}
    for f in tree["files"]:
        for dep in f.get("fetchcontent", []):
            deps_by_name.setdefault(dep["name"], dep)
    deps = []
    failures = []
    for name in sorted(deps_by_name):
        dep = deps_by_name[name]
        archive = dep.get("url", "")
        expected = (dep.get("url_hash") or "").lower()
        actual = hashlib.sha256((vendor / archive).read_bytes()).hexdigest()
        pin_val = pin_map.get(name.lower(), "")
        ok = actual == expected and actual == pin_val
        if not ok:
            failures.append(name)
        deps.append(
            {
                "name": name,
                "archive": archive,
                "url_hash_expected": expected,
                "url_hash_actual": actual,
                "pin_field": "git_commit",
                "pin_value": pin_val,
                "ok": ok,
            }
        )
    failures = sorted(failures)
    audit = {"deps": deps, "failures": failures}
    snap = {
        "version": 1,
        "audited_names": [d["name"] for d in deps],
        "failures": failures,
    }
    return audit, snap


def reference_scan(tree: dict, prefix: Path) -> dict:
    artifacts = []
    for full in sorted(prefix.rglob("*")):
        if full.is_dir() and not full.is_symlink():
            continue
        if not (full.is_file() or full.is_symlink()):
            continue
        rel = full.relative_to(prefix).as_posix()
        if full.is_symlink():
            artifacts.append({"path": rel, "kind": "symlink", "sha256": "-"})
        else:
            artifacts.append(
                {
                    "path": rel,
                    "kind": "file",
                    "sha256": hashlib.sha256(full.read_bytes()).hexdigest(),
                }
            )
    artifacts.sort(key=lambda a: a["path"])
    names = sorted(
        {
            d["name"]
            for f in tree["files"]
            for d in f.get("fetchcontent", [])
        }
    )
    return {
        "prefix": str(prefix),
        "artifacts": artifacts,
        "fetch_deps": names,
        "transitive_closure": names,
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestParseStage:
    def test_ingest_snapshot_and_tree_match_reference(self) -> None:
        reset_state()
        out = APP / "data" / "cmake-tree.json"
        proc = _run(
            [str(BIN), "parse", str(PROJECT), "--output", str(out), "--strict"]
        )
        assert proc.returncode == 0, proc.stderr
        snap = APP / "state" / "cmake-ingest-snapshot.json"
        assert snap.is_file()
        expect_ingest = reference_ingest(PROJECT)
        got_ingest = load_json(snap)
        assert got_ingest["version"] == 1
        assert got_ingest["root"] == expect_ingest["root"]
        assert [f["path"] for f in got_ingest["files"]] == [
            f["path"] for f in expect_ingest["files"]
        ]
        assert got_ingest == expect_ingest
        assert load_json(out) == reference_tree(expect_ingest)

    def test_nested_gadget_and_declaration_order(self) -> None:
        reset_state()
        out = APP / "data" / "cmake-tree.json"
        assert _run([str(BIN), "parse", str(PROJECT), "--output", str(out), "--strict"]).returncode == 0
        tree = load_json(out)
        paths = [f["path"] for f in tree["files"]]
        assert "third_party/widget/gadget/CMakeLists.txt" in paths
        widget = next(f for f in tree["files"] if f["path"] == "third_party/widget/CMakeLists.txt")
        assert [d["name"] for d in widget["fetchcontent"]] == ["libfoo", "libbar"]
        gadget = next(
            f for f in tree["files"] if f["path"] == "third_party/widget/gadget/CMakeLists.txt"
        )
        assert gadget["includes"] == ["cmake/WidgetHelpers.cmake"]

    def test_strict_malformed_aborts_without_output(self) -> None:
        reset_state()
        out = APP / "data" / "should-not-exist.json"
        if out.exists():
            out.unlink()
        proc = _run(
            [
                str(BIN),
                "parse",
                str(PROJECT / "bad" / "malformed"),
                "--output",
                str(out),
                "--strict",
            ]
        )
        assert proc.returncode == 2
        assert not out.exists()

    def test_partial_ingest_only_fails_export_order(self) -> None:
        """Fixing ingest.sh alone while export_tree remains broken must fail."""
        reset_state()
        install_text(BROKEN_LIB / "export_tree.sh", LIB / "export_tree.sh")
        install_text(GOLDEN_LIB / "normalize.sh", LIB / "normalize.sh")
        install_text(GOLDEN_LIB / "ingest.sh", LIB / "ingest.sh")
        install_text(GOLDEN_BIN, BIN)
        out = APP / "data" / "cmake-tree.json"
        proc = _run([str(BIN), "parse", str(PROJECT), "--output", str(out), "--strict"])
        assert proc.returncode == 0, proc.stderr
        tree = load_json(out)
        widget = next(f for f in tree["files"] if f["path"] == "third_party/widget/CMakeLists.txt")
        names = [d["name"] for d in widget["fetchcontent"]]
        assert names != ["libfoo", "libbar"], "broken export re-sorts; trap must still be broken"


class TestHashStage:
    def _parse(self) -> Path:
        reset_state()
        out = APP / "data" / "cmake-tree.json"
        assert _run([str(BIN), "parse", str(PROJECT), "--output", str(out), "--strict"]).returncode == 0
        return out

    def test_hash_audit_matches_reference_and_writes_snapshot(self) -> None:
        tree_path = self._parse()
        out = APP / "data" / "hash-audit.json"
        proc = _run(
            [
                str(BIN),
                "hash-audit",
                "--tree",
                str(tree_path),
                "--vendor",
                str(VENDOR),
                "--pins",
                str(PINS),
                "--output",
                str(out),
            ]
        )
        assert proc.returncode == 0, proc.stderr
        snap = APP / "state" / "hash-audit-snapshot.json"
        assert snap.is_file()
        tree = load_json(tree_path)
        expect_audit, expect_snap = reference_hash(
            tree, VENDOR, PINS.read_text(encoding="utf-8")
        )
        assert load_json(out) == expect_audit
        assert load_json(snap) == expect_snap
        assert expect_audit["failures"] == []
        for dep in expect_audit["deps"]:
            assert dep["ok"] is True
            assert dep["pin_field"] == "git_commit"

    def test_ephemeral_vendor_digest(self, tmp_path: Path) -> None:
        tree_path = self._parse()
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        # copy archives but corrupt libfoo bytes
        for src in VENDOR.glob("*.tar.gz"):
            dst = vendor / src.name
            data = src.read_bytes()
            if src.name.startswith("libfoo"):
                data = data + b"\x00"
            dst.write_bytes(data)
        pins = tmp_path / "pins.cmake"
        pins.write_text(PINS.read_text(encoding="utf-8"), encoding="utf-8")
        out = tmp_path / "hash.json"
        proc = _run(
            [
                str(BIN),
                "hash-audit",
                "--tree",
                str(tree_path),
                "--vendor",
                str(vendor),
                "--pins",
                str(pins),
                "--output",
                str(out),
            ]
        )
        assert proc.returncode == 0, proc.stderr
        audit = load_json(out)
        assert "libfoo" in audit["failures"]
        foo = next(d for d in audit["deps"] if d["name"] == "libfoo")
        assert foo["ok"] is False
        assert foo["url_hash_actual"] == hashlib.sha256(
            (vendor / foo["archive"]).read_bytes()
        ).hexdigest()

    def test_uses_git_commit_not_tag(self) -> None:
        tree_path = self._parse()
        out = APP / "data" / "hash-audit.json"
        assert (
            _run(
                [
                    str(BIN),
                    "hash-audit",
                    "--tree",
                    str(tree_path),
                    "--vendor",
                    str(VENDOR),
                    "--pins",
                    str(PINS),
                    "--output",
                    str(out),
                ]
            ).returncode
            == 0
        )
        for dep in load_json(out)["deps"]:
            assert not dep["pin_value"].startswith("v")
            assert re.fullmatch(r"[0-9a-f]{64}", dep["pin_value"])


class TestScanStage:
    def _pipeline(self) -> Path:
        reset_state()
        tree = APP / "data" / "cmake-tree.json"
        assert _run([str(BIN), "parse", str(PROJECT), "--output", str(tree), "--strict"]).returncode == 0
        assert (
            _run(
                [
                    str(BIN),
                    "hash-audit",
                    "--tree",
                    str(tree),
                    "--vendor",
                    str(VENDOR),
                    "--pins",
                    str(PINS),
                    "--output",
                    str(APP / "data" / "hash-audit.json"),
                ]
            ).returncode
            == 0
        )
        return tree

    def test_install_manifest_matches_reference(self) -> None:
        tree_path = self._pipeline()
        out = APP / "output" / "install-manifest.json"
        proc = _run(
            [
                str(BIN),
                "scan",
                "--tree",
                str(tree_path),
                "--prefix",
                str(INSTALL),
                "--output",
                str(out),
            ]
        )
        assert proc.returncode == 0, proc.stderr
        got = load_json(out)
        expect = reference_scan(load_json(tree_path), INSTALL)
        assert got == expect
        assert "libbaz" in got["transitive_closure"]
        assert got["fetch_deps"] == got["transitive_closure"]
        sym = [a for a in got["artifacts"] if a["kind"] == "symlink"]
        assert sym, "expected at least one symlink artifact"
        assert all(a["sha256"] == "-" for a in sym)

    def test_scan_gates_on_hash_failures(self) -> None:
        tree_path = self._pipeline()
        snap = APP / "state" / "hash-audit-snapshot.json"
        data = load_json(snap)
        data["failures"] = ["libfoo"]
        snap.write_text(json.dumps(data), encoding="utf-8")
        out = APP / "output" / "blocked.json"
        if out.exists():
            out.unlink()
        proc = _run(
            [
                str(BIN),
                "scan",
                "--tree",
                str(tree_path),
                "--prefix",
                str(INSTALL),
                "--output",
                str(out),
            ]
        )
        assert proc.returncode != 0
        assert not out.exists()

    def test_partial_closure_only_leaves_scan_broken(self) -> None:
        """Golden fetch_closure with broken scan must still fail (gate/symlinks)."""
        reset_state()
        install_text(GOLDEN_LIB / "fetch_closure.sh", LIB / "fetch_closure.sh")
        install_text(BROKEN_LIB / "scan.sh", LIB / "scan.sh")
        install_text(GOLDEN_LIB / "hash.sh", LIB / "hash.sh")
        install_text(GOLDEN_LIB / "ingest.sh", LIB / "ingest.sh")
        install_text(GOLDEN_LIB / "export_tree.sh", LIB / "export_tree.sh")
        install_text(GOLDEN_LIB / "normalize.sh", LIB / "normalize.sh")
        install_text(GOLDEN_BIN, BIN)
        tree_path = APP / "data" / "cmake-tree.json"
        assert _run([str(BIN), "parse", str(PROJECT), "--output", str(tree_path), "--strict"]).returncode == 0
        assert (
            _run(
                [
                    str(BIN),
                    "hash-audit",
                    "--tree",
                    str(tree_path),
                    "--vendor",
                    str(VENDOR),
                    "--pins",
                    str(PINS),
                    "--output",
                    str(APP / "data" / "hash-audit.json"),
                ]
            ).returncode
            == 0
        )
        out = APP / "output" / "install-manifest.json"
        _run(
            [
                str(BIN),
                "scan",
                "--tree",
                str(tree_path),
                "--prefix",
                str(INSTALL),
                "--output",
                str(out),
            ]
        )
        # Broken scan ignores gate and misses symlinks / nested closure depending on stub.
        if out.exists():
            got = load_json(out)
            expect = reference_scan(load_json(tree_path), INSTALL)
            assert got != expect


class TestEndToEnd:
    def test_full_pipeline(self) -> None:
        reset_state()
        tree = APP / "data" / "cmake-tree.json"
        audit = APP / "data" / "hash-audit.json"
        manifest = APP / "output" / "install-manifest.json"
        assert _run([str(BIN), "parse", str(PROJECT), "--output", str(tree), "--strict"]).returncode == 0
        assert (
            _run(
                [
                    str(BIN),
                    "hash-audit",
                    "--tree",
                    str(tree),
                    "--vendor",
                    str(VENDOR),
                    "--pins",
                    str(PINS),
                    "--output",
                    str(audit),
                ]
            ).returncode
            == 0
        )
        assert (
            _run(
                [
                    str(BIN),
                    "scan",
                    "--tree",
                    str(tree),
                    "--prefix",
                    str(INSTALL),
                    "--output",
                    str(manifest),
                ]
            ).returncode
            == 0
        )
        ingest = reference_ingest(PROJECT)
        assert load_json(APP / "state" / "cmake-ingest-snapshot.json") == ingest
        assert load_json(tree) == reference_tree(ingest)
        expect_audit, expect_snap = reference_hash(
            load_json(tree), VENDOR, PINS.read_text(encoding="utf-8")
        )
        assert load_json(audit) == expect_audit
        assert load_json(APP / "state" / "hash-audit-snapshot.json") == expect_snap
        assert load_json(manifest) == reference_scan(load_json(tree), INSTALL)

    def test_demo_build_still_works(self) -> None:
        proc = _run(["cmake", "--build", "/app/build"])
        assert proc.returncode == 0, proc.stderr
