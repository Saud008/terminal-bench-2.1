"""Checks zonec against canonical listings for master files it has not seen.

Expected listings were produced from the rules in /app/docs and cross-checked
against dnspython 2.7 and BIND 9.18 named-compilezone where those follow the
same rules; every ZONEMD digest was recomputed from the listing with
dnspython's RFC 8976 implementation."""

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

APP = Path("/app")
BUILD = Path("/tmp/zonec-verify-build")
CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["groups"]

FORBIDDEN_CALLS = re.compile(
    r"\b(system|popen|execl|execlp|execle|execv|execvp|execvpe|execve|fexecve|fork|vfork"
    r"|posix_spawn|posix_spawnp|dlopen)\s*\("
)


def _hide_reference_tools():
    for name in ("named-compilezone", "named-checkzone", "ldns-read-zone", "kzonecheck"):
        while True:
            path = shutil.which(name)
            if not path:
                break
            os.rename(path, path + ".hidden-by-check")


def _strip_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def _source_policy_problems():
    problems = []
    for src in sorted((APP / "src").rglob("*")):
        if src.suffix not in (".c", ".h"):
            continue
        code = _strip_comments(src.read_text(encoding="utf-8", errors="replace"))
        match = FORBIDDEN_CALLS.search(code)
        if match:
            problems.append(f"{src.relative_to(APP)} calls {match.group(1)}()")
    return problems


@pytest.fixture(scope="session")
def zonec():
    _hide_reference_tools()
    problems = _source_policy_problems()
    assert not problems, "source policy: " + "; ".join(problems)
    shutil.rmtree(BUILD, ignore_errors=True)
    build = subprocess.run(
        ["make", "-C", str(APP), f"BUILD={BUILD}"],
        capture_output=True, text=True, timeout=600,
    )
    assert build.returncode == 0, "make failed:\n" + build.stderr[-4000:]
    binary = BUILD / "zonec"
    assert binary.is_file(), f"make did not produce {binary}"
    return str(binary)


def _run_case(binary, case):
    base = Path(tempfile.mkdtemp(prefix="zonec-case-"))
    elsewhere = Path(tempfile.mkdtemp(prefix="zonec-cwd-"))
    for rel, text in case["files"].items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    proc = subprocess.run(
        [binary, "-o", case["origin"], str(base / case["entry"])],
        capture_output=True, text=True, cwd=elsewhere, timeout=60,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "LC_ALL": "C"},
    )
    return base, proc


def _check_group(binary, group):
    failures = []
    for case in CASES[group]:
        base, proc = _run_case(binary, case)
        label = f"--- {group}/{case['name']} (zonec -o {case['origin']} {case['entry']})"
        if case["error_line"] is None:
            if (proc.returncode, proc.stdout) != (0, case["stdout"]):
                failures.append(
                    f"{label}\nexpected exit 0 and:\n{case['stdout']}"
                    f"got exit {proc.returncode}, stderr {proc.stderr.strip()!r}, stdout:\n{proc.stdout}"
                )
            continue
        prefix = f"{base / case['error_file']}:{case['error_line']}: "
        first = proc.stderr.splitlines()[0] if proc.stderr else ""
        if proc.returncode != 1 or proc.stdout != "" or not first.startswith(prefix):
            failures.append(
                f"{label}\nexpected exit 1, empty stdout and a diagnostic starting with {prefix!r}\n"
                f"got exit {proc.returncode}, stderr {first!r}, stdout:\n{proc.stdout}"
            )
    assert not failures, f"{len(failures)} of {len(CASES[group])} cases differ:\n" + "\n".join(failures)


def test_owner_continuation(zonec):
    """Indented records keep the previous record's owner across $ORIGIN changes (relative and absolute)."""
    _check_group(zonec, "owner_continuation")


def test_default_ttl(zonec):
    """Records without a TTL use $TTL first, then the last written TTL, then the SOA minimum; none is an error."""
    _check_group(zonec, "default_ttl")


def test_include_scope(zonec):
    """$TTL values and record TTLs inside an included file do not affect lines after the $INCLUDE."""
    _check_group(zonec, "include_scope")


def test_include_paths(zonec):
    """Relative $INCLUDE paths resolve against the including file's directory, nested and with '..', and errors name the included file."""
    _check_group(zonec, "include_paths")


def test_quoted_parentheses(zonec):
    """Parentheses and semicolons inside quoted strings are text; a really unbalanced parenthesis is still reported."""
    _check_group(zonec, "quoted_parentheses")


def test_escaped_case(zonec):
    """Names written with \\DDD escapes fold to lowercase like plain letters, in owners and in RDATA, and deduplicate."""
    _check_group(zonec, "escaped_case")


def test_escaped_label_length(zonec):
    """Label length is counted in decoded octets: 63-octet escaped labels are accepted, 64-octet labels rejected at their line."""
    _check_group(zonec, "escaped_label_length")


def test_canonical_order(zonec):
    """Records are sorted in RFC 4034 canonical name order, then by type code, then by RDATA wire form."""
    _check_group(zonec, "canonical_order")


def test_rrset_ttl(zonec):
    """Every record of an RRset takes the TTL of the RRset's first record in input order, includes expanded in place."""
    _check_group(zonec, "rrset_ttl")


def test_zonemd(zonec):
    """The apex ZONEMD gets the SOA serial and the RFC 8976 SHA-384 digest of the listing; other ZONEMD records are data; SHA-512 at the apex is rejected."""
    _check_group(zonec, "zonemd")


def test_reference_zone(zonec):
    """A multi-file production-style zone combining includes with origins, $TTL scopes, escapes, multi-line records and a ZONEMD digest."""
    _check_group(zonec, "reference_zone")
