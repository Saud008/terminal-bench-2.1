"""Checks quire against output recorded from editorconfig 0.12.6
(Debian bookworm package 0.12.6-0.1) on the same trees and arguments."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = Path("/tmp/quire-verify")
BINARY = OUT / "quire"
BASE = Path("/srv/qc")
CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["groups"]

FORBIDDEN_IMPORTS = re.compile(r'"(os/exec|syscall|unsafe|plugin|C|golang\.org/x/sys/[^"]*)"')


def _hide_reference_tools():
    for name in ("editorconfig",):
        while True:
            path = shutil.which(name)
            if not path:
                break
            os.rename(path, path + ".hidden-by-verifier")


def _strip_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def _source_policy_problems():
    problems = []
    gomod = (APP / "go.mod").read_text(encoding="utf-8")
    if re.search(r"^\s*(require|replace)\b", gomod, flags=re.M):
        problems.append("go.mod declares module dependencies")
    if (APP / "vendor").exists():
        problems.append("vendor directory present")
    for src in sorted(APP.rglob("*.go")):
        rel = src.relative_to(APP)
        raw = src.read_text(encoding="utf-8")
        if re.search(r"^//go:(linkname|cgo_)", raw, flags=re.M):
            problems.append(f"{rel} uses a compiler directive")
        for m in FORBIDDEN_IMPORTS.finditer(_strip_comments(raw)):
            problems.append(f"{rel} imports {m.group(1)}")
    return problems


@pytest.fixture(scope="session")
def quire():
    _hide_reference_tools()
    problems = _source_policy_problems()
    assert not problems, "source policy: " + "; ".join(problems)
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    env = dict(os.environ, GOTOOLCHAIN="local", GOPROXY="off", GOFLAGS="-buildvcs=false",
               CGO_ENABLED="0", GOCACHE=str(OUT / "cache"))
    build = subprocess.run(["go", "build", "-o", str(BINARY), "./cmd/quire"],
                           cwd=APP, env=env, capture_output=True, text=True, timeout=1800)
    assert build.returncode == 0, "go build failed:\n" + build.stderr[-4000:]
    assert BINARY.is_file()
    for stray in (Path("/.editorconfig"), Path("/srv/.editorconfig")):
        if stray.is_file():
            stray.unlink()
    return str(BINARY)


def _run_case(binary, case):
    root = BASE / case["id"]
    shutil.rmtree(root, ignore_errors=True)
    for rel, text in case["files"].items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    args = [a.replace("{root}", str(root)) for a in case["args"]]
    stdin = case.get("stdin", "").replace("{root}", str(root))
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
    p = subprocess.run([binary, *args], input=stdin.encode("utf-8"), capture_output=True,
                       env=env, timeout=60)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def _check_group(binary, group):
    failures = []
    for case in CASES[group]:
        rc, out, err = _run_case(binary, case)
        if (rc, out, err) != (case["rc"], case["stdout"], case["stderr"]):
            failures.append(
                f"--- {case['id']} args={case['args']} stdin={case.get('stdin')!r}\n"
                f"expected rc={case['rc']} stderr={case['stderr']!r}\n{case['stdout']}"
                f"got rc={rc} stderr={err!r}\n{out}"
            )
    assert not failures, f"{len(failures)} of {len(CASES[group])} cases differ:\n" + "\n".join(failures)


def test_section_anchoring(quire):
    """Headers with a '/' are anchored to their file's directory; others match at any depth."""
    _check_group(quire, "section_anchoring")


def test_tab_indentation(quire):
    """indent_size / tab_width derivation, with and without -b."""
    _check_group(quire, "tab_indentation")


def test_bracketed_directories(quire):
    """EditorConfig files in directories whose names contain glob characters."""
    _check_group(quire, "bracketed_directories")


def test_stdin_paths(quire):
    """File paths read from standard input."""
    _check_group(quire, "stdin_paths")


def test_globstar_segments(quire):
    """'/**/' matches zero or more directories."""
    _check_group(quire, "globstar_segments")


def test_negated_classes(quire):
    """Bracket expressions: '[!...]' negation, literal '^', brackets containing '/'."""
    _check_group(quire, "negated_classes")


def test_inline_comments(quire):
    """Comment, header and property line syntax, limits and syntax errors."""
    _check_group(quire, "inline_comments")


def test_root_declarations(quire):
    """root = true in a preamble; root inside a section."""
    _check_group(quire, "root_declarations")


def test_value_case(quire):
    """Which property values are lowercased."""
    _check_group(quire, "value_case")


def test_property_order(quire):
    """Output order when properties are overridden or derived."""
    _check_group(quire, "property_order")
