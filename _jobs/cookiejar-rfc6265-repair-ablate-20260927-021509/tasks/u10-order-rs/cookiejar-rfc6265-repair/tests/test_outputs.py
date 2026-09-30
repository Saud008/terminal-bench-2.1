"""Replays hidden transcripts through crumbjar and compares its output with
what an RFC 6265 user agent following /app/docs produces."""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
TARGET = Path("/tmp/crumbjar-verify-target")
BINARY = TARGET / "release" / "crumbjar"
CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["groups"]

FORBIDDEN_CODE = {
    "unsafe": re.compile(r"\bunsafe\b"),
    "extern": re.compile(r"\bextern\b"),
    "#[link]": re.compile(r"#\s*!?\s*\[\s*link\b"),
    "process::Command": re.compile(r"\bprocess\s*::\s*(?:Command\b|\{[^}]*\bCommand\b)"),
    "Command::new": re.compile(r"\bCommand\s*::\s*new\b"),
}


def _strip_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def _source_policy_problems():
    problems = []
    lock = (APP / "Cargo.lock").read_text(encoding="utf-8")
    packages = re.findall(r'^name = "([^"]+)"', lock, flags=re.M)
    if packages != ["crumbjar"]:
        problems.append(f"Cargo.lock lists packages other than crumbjar: {packages}")
    for rs in sorted(APP.rglob("*.rs")):
        rel = rs.relative_to(APP)
        if rel.parts[0] == "target":
            continue
        code = _strip_comments(rs.read_text(encoding="utf-8"))
        for name, pattern in FORBIDDEN_CODE.items():
            if pattern.search(code):
                problems.append(f"{rel} uses {name}")
    return problems


@pytest.fixture(scope="session")
def crumbjar():
    problems = _source_policy_problems()
    assert not problems, "source policy: " + "; ".join(problems)
    env = dict(os.environ, CARGO_TARGET_DIR=str(TARGET))
    build = subprocess.run(
        ["cargo", "build", "--release", "--offline", "--locked"],
        cwd=APP, env=env, capture_output=True, text=True, timeout=1800,
    )
    assert build.returncode == 0, "cargo build failed:\n" + build.stderr[-4000:]
    assert BINARY.is_file()
    return str(BINARY)


def _check_group(binary, group):
    failures = []
    for case in CASES[group]:
        p = subprocess.run(
            [binary, "replay", "-"],
            input=case["transcript"], capture_output=True, text=True, timeout=60,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "LC_ALL": "C"},
        )
        if p.returncode != 0 or p.stdout != case["stdout"]:
            failures.append(
                f"--- transcript\n{case['transcript']}"
                f"--- expected (exit 0)\n{case['stdout']}"
                f"--- got (exit {p.returncode})\n{p.stdout}{p.stderr[-500:]}"
            )
    assert not failures, f"{len(failures)} of {len(CASES[group])} transcripts differ:\n" + "\n".join(failures)


def test_default_path(crumbjar):
    """Cookies without a usable Path attribute get the directory of the request path as their path."""
    _check_group(crumbjar, "default_path")


def test_path_boundary(crumbjar):
    """A cookie path only matches request paths that continue it at a '/' boundary."""
    _check_group(crumbjar, "path_boundary")


def test_host_only(crumbjar):
    """Cookies set without a Domain attribute go back only to the exact host that set them."""
    _check_group(crumbjar, "host_only")


def test_ip_hosts(crumbjar):
    """IP-address hosts only domain-match themselves, so suffix Domain attributes from them are ignored."""
    _check_group(crumbjar, "ip_hosts")


def test_max_age_precedence(crumbjar):
    """Max-Age decides the lifetime over Expires regardless of attribute order; invalid Max-Age is skipped."""
    _check_group(crumbjar, "max_age_precedence")


def test_two_digit_years(crumbjar):
    """Two-digit years in Expires map 70-99 to 19xx and 00-69 to 20xx."""
    _check_group(crumbjar, "two_digit_years")


def test_invalid_dates(crumbjar):
    """Expires dates that do not exist on the Gregorian calendar are ignored; real leap days are kept."""
    _check_group(crumbjar, "invalid_dates")


def test_replacement(crumbjar):
    """Replacing a cookie keeps the old creation-time, which shows in header order and the dump."""
    _check_group(crumbjar, "replacement")


def test_header_order(crumbjar):
    """Cookie header lists longer paths first and equal paths by creation-time."""
    _check_group(crumbjar, "header_order")


def test_public_suffix(crumbjar):
    """Domain attributes naming a public suffix are refused, except when it is the request host itself."""
    _check_group(crumbjar, "public_suffix")


def test_site_limit(crumbjar):
    """Per-site limit of docs/POLICY.md evicts the least recently accessed cookie of the site."""
    _check_group(crumbjar, "site_limit")


def test_name_value_pair(crumbjar):
    """Set-Cookie headers without '=' in the first pair, or with an empty name, are ignored."""
    _check_group(crumbjar, "name_value_pair")
