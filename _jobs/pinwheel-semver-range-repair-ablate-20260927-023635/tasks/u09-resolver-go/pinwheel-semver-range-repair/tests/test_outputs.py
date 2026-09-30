"""Checks pinwheel against expectations recorded from node-semver 7.6.3 and
against locks computed independently from the rules in /app/docs."""

import difflib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
REGISTRY = FIXTURES / "registry"
BUILD_DIR = Path("/tmp/pinwheel-verify")
BINARY = BUILD_DIR / "pinwheel"
CASES = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
ENV = {
    "PATH": "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin",
    "HOME": "/root",
    "LC_ALL": "C",
    "GOTOOLCHAIN": "local",
    "GOPROXY": "off",
    "GOFLAGS": "",
    "CGO_ENABLED": "0",
    "GOCACHE": str(BUILD_DIR / "gocache"),
}
FORBIDDEN_IMPORTS = re.compile(r'"(os/exec|syscall|unsafe|plugin|C)"')


def _source_policy_problems():
    problems = []
    gomod = (APP / "go.mod").read_text(encoding="utf-8")
    if re.search(r"^\s*require\b", gomod, flags=re.M):
        problems.append("go.mod declares module requirements")
    for src in sorted(APP.rglob("*.go")):
        if src.name.endswith("_test.go"):
            continue
        if FORBIDDEN_IMPORTS.search(src.read_text(encoding="utf-8")):
            problems.append(f"{src.relative_to(APP)} imports a forbidden package")
    return problems


@pytest.fixture(scope="session")
def pinwheel():
    problems = _source_policy_problems()
    assert not problems, "source policy: " + "; ".join(problems)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    build = subprocess.run(
        ["go", "build", "-o", str(BINARY), "./cmd/pinwheel"],
        cwd=APP, env=ENV, capture_output=True, text=True, timeout=1800,
    )
    assert build.returncode == 0, "go build failed:\n" + build.stderr[-4000:]
    return str(BINARY)


def _run(binary, *args):
    p = subprocess.run([binary, *args], capture_output=True, text=True, env=ENV, timeout=60)
    return p.returncode, p.stdout, p.stderr


def _check_satisfies(binary, group):
    rows = CASES["satisfies"][group]
    failures = []
    for version, rng, want in rows:
        rc, out, err = _run(binary, "satisfies", version, rng)
        expected = "true\n" if want else "false\n"
        if (rc, out) != (0, expected):
            failures.append(
                f"satisfies {version!r} {rng!r}: expected rc=0 {expected.strip()}, "
                f"got rc={rc} stdout={out.strip()!r} stderr={err.strip()!r}"
            )
    assert not failures, f"{len(failures)} of {len(rows)} cases differ:\n" + "\n".join(failures)


def _check_compare(binary, group):
    rows = CASES["compare"][group]
    failures = []
    for a, b, want in rows:
        rc, out, err = _run(binary, "compare", a, b)
        if (rc, out) != (0, f"{want}\n"):
            failures.append(
                f"compare {a!r} {b!r}: expected rc=0 {want}, got rc={rc} stdout={out.strip()!r} stderr={err.strip()!r}"
            )
    assert not failures, f"{len(failures)} of {len(rows)} cases differ:\n" + "\n".join(failures)


def _resolve(binary, name, tmp_path):
    project = tmp_path / name
    shutil.copytree(FIXTURES / "projects" / name, project)
    rc, out, err = _run(binary, "resolve", "--registry", str(REGISTRY), str(project))
    return rc, out, err, project / "pin.lock"


def _check_lock(binary, name, tmp_path):
    expected = (FIXTURES / "expected" / f"{name}.lock").read_text(encoding="utf-8")
    count = len(json.loads(expected)["packages"])
    rc, out, err, lock = _resolve(binary, name, tmp_path)
    assert rc == 0, f"resolve {name}: exit {rc}, stderr: {err.strip()}"
    assert out == f"resolved {count} packages\n", f"resolve {name}: stdout {out!r}"
    assert lock.is_file(), f"resolve {name}: no pin.lock written"
    actual = lock.read_text(encoding="utf-8")
    diff = "".join(difflib.unified_diff(
        expected.splitlines(True), actual.splitlines(True), "expected pin.lock", "actual pin.lock"))
    assert actual == expected, f"resolve {name}: lock differs\n{diff}"


def test_caret_ranges(pinwheel):
    """Caret ranges, including 0.x and 0.0.x versions, partials and prereleases, match node-semver."""
    _check_satisfies(pinwheel, "caret")


def test_tilde_ranges(pinwheel):
    """Tilde ranges (~, ~>, major-only and major.minor forms) match node-semver."""
    _check_satisfies(pinwheel, "tilde")


def test_partial_version_comparators(pinwheel):
    """Operators applied to partial versions (>1.2, <=1, <1.2, 1.x, *) match node-semver."""
    _check_satisfies(pinwheel, "partial_comparators")


def test_hyphen_ranges(pinwheel):
    """Hyphen ranges with full and partial ends match node-semver."""
    _check_satisfies(pinwheel, "hyphen")


def test_prerelease_admission(pinwheel):
    """Prereleases only match a set naming a prerelease of the same major.minor.patch."""
    _check_satisfies(pinwheel, "prerelease_admission")


def test_union_and_operator_spacing(pinwheel):
    """'||' with or without surrounding spaces, spaces after operators and the empty range."""
    _check_satisfies(pinwheel, "unions_and_spacing")


def test_build_metadata_ignored(pinwheel):
    """Build metadata affects neither range matching nor compare output."""
    _check_satisfies(pinwheel, "build_metadata")
    _check_compare(pinwheel, "build_metadata")


def test_prerelease_precedence(pinwheel):
    """compare orders prereleases by SemVer 2.0.0 precedence (numeric ids, longer sets, v prefix)."""
    _check_compare(pinwheel, "precedence")


def test_invalid_input_rejected(pinwheel):
    """Strictly invalid versions and ranges exit 2 with the documented message; valid ones are accepted."""
    inv = CASES["invalid"]
    failures = []
    for v in inv["versions"]:
        for args in (["satisfies", v, "*"], ["compare", v, "1.0.0"]):
            rc, out, err = _run(pinwheel, *args)
            if rc != 2 or out or not err.startswith(f'pinwheel: invalid version "{v}"'):
                failures.append(f"{args}: expected exit 2 invalid version, got rc={rc} stdout={out!r} stderr={err.strip()!r}")
    for r in inv["ranges"]:
        rc, out, err = _run(pinwheel, "satisfies", "1.0.0", r)
        if rc != 2 or out or not err.startswith(f'pinwheel: invalid range "{r}"'):
            failures.append(f"satisfies 1.0.0 {r!r}: expected exit 2 invalid range, got rc={rc} stdout={out!r} stderr={err.strip()!r}")
    for v in inv["valid_versions"]:
        rc, out, err = _run(pinwheel, "satisfies", v, "*")
        if rc != 0 or out not in ("true\n", "false\n"):
            failures.append(f"satisfies {v!r} '*': valid version rejected, rc={rc} stderr={err.strip()!r}")
    for r in inv["valid_ranges"]:
        rc, out, err = _run(pinwheel, "satisfies", "1.0.0", r)
        if rc != 0 or out not in ("true\n", "false\n"):
            failures.append(f"satisfies 1.0.0 {r!r}: valid range rejected, rc={rc} stderr={err.strip()!r}")
    assert not failures, "\n".join(failures)


def test_lock_drops_packages_no_longer_required(pinwheel, tmp_path):
    """Packages no longer required after a later round downgrades a release are dropped from the lock."""
    _check_lock(pinwheel, "prune", tmp_path)


def test_lock_applies_overrides(pinwheel, tmp_path):
    """An override replaces the dependents' ranges and never adds a package by itself."""
    _check_lock(pinwheel, "overrides", tmp_path)


def test_lock_yanked_releases(pinwheel, tmp_path):
    """Yanked releases are skipped unless an exact pin (bare or '=') names them."""
    _check_lock(pinwheel, "yanked", tmp_path)


def test_lock_prefer_lowest_and_ties(pinwheel, tmp_path):
    """prefer=lowest picks lowest releases; equal-precedence ties go to latest published, then file order."""
    _check_lock(pinwheel, "lowest", tmp_path)


def test_lock_mixed_range_forms(pinwheel, tmp_path):
    """A project using caret, tilde, hyphen, partial, union, prerelease and build-metadata ranges locks correctly."""
    _check_lock(pinwheel, "mixed", tmp_path)


def test_resolution_failures(pinwheel, tmp_path):
    """Unsatisfiable and unknown packages exit 3 with the documented message and leave pin.lock alone."""
    _check_lock(pinwheel, "small", tmp_path)

    sentinel = '{"lockfileVersion": 1, "name": "previous", "packages": {}}\n'
    for name, message in (
        ("unsat", 'pinwheel: no version of quartz-http satisfies "^0.3.1" (from <root>)'),
        ("missing", 'pinwheel: unknown package "ghost-pkg" (required by <root>)'),
    ):
        project = tmp_path / name
        shutil.copytree(FIXTURES / "projects" / name, project)
        (project / "pin.lock").write_text(sentinel, encoding="utf-8")
        rc, out, err = _run(pinwheel, "resolve", "--registry", str(REGISTRY), str(project))
        assert rc == 3, f"resolve {name}: expected exit 3, got {rc} (stdout {out!r}, stderr {err.strip()!r})"
        assert out == "", f"resolve {name}: unexpected stdout {out!r}"
        assert err.strip() == message, f"resolve {name}: expected stderr {message!r}, got {err.strip()!r}"
        assert (project / "pin.lock").read_text(encoding="utf-8") == sentinel, f"resolve {name}: pin.lock was modified"
