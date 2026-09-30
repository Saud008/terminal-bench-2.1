"""Checks gleaner against output recorded from git (`git ls-files --others
--exclude-standard` and `git check-ignore -v -n`, run at the top of freshly
initialised work trees with nothing tracked; git 2.39.5 and 2.53.0 print
the same for every tree)."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
TARGET = Path("/tmp/gleaner-verify-target")
BINARY = TARGET / "release" / "gleaner"
BASE = Path("/tmp/gleaner-case")
REPO = BASE / "repo"
HOME = BASE / "user"
XDG = BASE / "xdg"
DEFAULT_CONFIG = "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n"
CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["groups"]


def _hide_reference_tools():
    for name in ("git",):
        while True:
            path = shutil.which(name)
            if not path:
                break
            os.rename(path, path + ".hidden-by-verifier")


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
    if packages != ["gleaner"]:
        problems.append(f"Cargo.lock lists packages other than gleaner: {packages}")
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
def gleaner():
    _hide_reference_tools()
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


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def _materialize(case):
    shutil.rmtree(BASE, ignore_errors=True)
    (REPO / ".git" / "info").mkdir(parents=True)
    HOME.mkdir(parents=True)
    _write(REPO / ".git" / "config", case.get("config", DEFAULT_CONFIG))
    if "exclude" in case:
        _write(REPO / ".git" / "info" / "exclude", case["exclude"])
    for rel, text in case["files"].items():
        _write(REPO / rel, text)
    for rel, text in case.get("home", {}).items():
        _write(HOME / rel, text)
    for rel, text in case.get("xdg", {}).items():
        _write(XDG / rel, text)


def _run(binary, case, args):
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(HOME), "LC_ALL": "C", **case.get("env", {})}
    p = subprocess.run([binary, *args], cwd=REPO, env=env, capture_output=True, timeout=60)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def _check_group(binary, group):
    failures = []
    for case in CASES[group]:
        _materialize(case)
        rc, out, err = _run(binary, case, ["list"])
        if (rc, out) != (0, case["list"]):
            failures.append(f"--- {case['name']}: list\nexpected rc=0\n{case['list']}got rc={rc} {err}\n{out}")
        rc, out, err = _run(binary, case, ["check", "--", *case["checks"]])
        if (rc, out) != (case["check_rc"], case["check"]):
            failures.append(
                f"--- {case['name']}: check {case['checks']}\n"
                f"expected rc={case['check_rc']}\n{case['check']}got rc={rc} {err}\n{out}"
            )
    assert not failures, f"{len(failures)} mismatches in {len(CASES[group])} trees:\n" + "\n".join(failures)


def test_file_encodings(gleaner):
    """Files with a UTF-8 byte order mark and CRLF line endings, including an unterminated last line."""
    _check_group(gleaner, "file_encodings")


def test_trailing_spaces(gleaner):
    """Only unescaped trailing spaces are dropped; tabs and backslash-escaped spaces stay in the pattern."""
    _check_group(gleaner, "trailing_spaces")


def test_escaped_leading_characters(gleaner):
    """`\\!` and `\\#` at the start of a line match names beginning with `!` and `#` instead of negating or commenting."""
    _check_group(gleaner, "escaped_leading_characters")


def test_directory_only_patterns(gleaner):
    """A trailing slash restricts a pattern to directories without anchoring it, at any depth."""
    _check_group(gleaner, "directory_only_patterns")


def test_anchoring(gleaner):
    """Patterns with a leading or middle slash match relative to the directory of the file that holds them."""
    _check_group(gleaner, "anchoring")


def test_double_star(gleaner):
    """`**` as a whole component matches zero or more directories; any other run of stars acts like `*`."""
    _check_group(gleaner, "double_star")


def test_bracket_expressions(gleaner):
    """Bracket sets: `^` and `!` negation, a leading `]` member, ranges and POSIX classes."""
    _check_group(gleaner, "bracket_expressions")


def test_reinclude_under_excluded_directory(gleaner):
    """Nothing inside an excluded directory can be re-included, and its .gitignore files are not read."""
    _check_group(gleaner, "reinclude_under_excluded_directory")


def test_per_directory_precedence(gleaner):
    """A deeper .gitignore overrides a shallower one, for negations and plain patterns alike."""
    _check_group(gleaner, "per_directory_precedence")


def test_tree_wide_sources(gleaner):
    """.gitignore beats .git/info/exclude, which beats the excludes file (absolute, ~/ and relative paths)."""
    _check_group(gleaner, "tree_wide_sources")


def test_default_excludes_file(gleaner):
    """Without core.excludesFile the file is $XDG_CONFIG_HOME/git/ignore, or $HOME/.config/git/ignore when XDG_CONFIG_HOME is unset or empty."""
    _check_group(gleaner, "default_excludes_file")


def test_config_spelling(gleaner):
    """core.excludesFile is found with any capitalisation of section and key, quoted values, and the last assignment wins."""
    _check_group(gleaner, "config_spelling")


def test_list_order(gleaner):
    """`list` sorts by the bytes of the whole path, so punctuation below `/` sorts ahead of a subdirectory."""
    _check_group(gleaner, "list_order")


def test_check_line_numbers(gleaner):
    """`check` reports physical line numbers, counting blank and comment lines."""
    _check_group(gleaner, "check_line_numbers")


def test_mixed_trees(gleaner):
    """Randomly generated trees combining nested .gitignore files, info/exclude and excludes files."""
    _check_group(gleaner, "mixed_trees")
