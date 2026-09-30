"""Verifier for hopcfg: compare its output with recorded Debian ssh -G output.

Every case in cases.json was produced by running
`ssh -G -F /root/.ssh/<cfg> ... <host>` from openssh-client 1:9.2p1-2+deb12u10
as root with the same config tree, keeping only the keywords hopcfg prints.
"""
import difflib
import glob
import json
import os
import re
import shutil
import subprocess
import tempfile

import pytest

TESTS_DIR = os.environ.get("TEST_DIR", "/tests")
SRC_DIR = "/app/src"
SSH_DIR = "/root/.ssh"
FIXTURE_ROOTS = [SSH_DIR, "/srv/hopcfg-fixture"]
SSH_BINARIES = ["/usr/bin/ssh", "/usr/local/bin/ssh", "/bin/ssh"]
FORBIDDEN_CALL = re.compile(
    r"\b(system|popen|execl|execlp|execle|execv|execvp|execve|execvpe|"
    r"fexecve|fork|vfork|posix_spawn|posix_spawnp|dlopen|syscall)\s*\(")
FORBIDDEN_HEADER = re.compile(r"#\s*include\s*<(spawn|dlfcn)\.h>")

with open(os.path.join(TESTS_DIR, "cases.json"), encoding="utf-8") as fh:
    GROUPS = json.load(fh)["groups"]


def _move_aside(paths):
    moved = []
    for path in paths:
        if os.path.lexists(path):
            aside = path + ".hopcfg-verifier"
            shutil.rmtree(aside, ignore_errors=True)
            os.rename(path, aside)
            moved.append((path, aside))
    return moved


def _restore(moved):
    for path, aside in moved:
        shutil.rmtree(path, ignore_errors=True)
        if os.path.lexists(path):
            os.unlink(path)
        os.rename(aside, path)


@pytest.fixture(scope="session")
def hopcfg():
    """Build /app/src with a fixed compiler command after checking the source policy."""
    sources = sorted(glob.glob(os.path.join(SRC_DIR, "*.c")))
    assert sources, f"no C sources in {SRC_DIR}"
    for path in sources + sorted(glob.glob(os.path.join(SRC_DIR, "*.h"))):
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        call = FORBIDDEN_CALL.search(text)
        assert call is None, f"{path}: hopcfg must not run other programs ({call.group(1)})"
        assert FORBIDDEN_HEADER.search(text) is None, f"{path}: forbidden header"
    build = tempfile.mkdtemp(prefix="hopcfg-verify-")
    binary = os.path.join(build, "hopcfg")
    proc = subprocess.run(["/usr/local/bin/gcc", "-std=c11", "-O2", "-w", "-o", binary,
                           *sources], capture_output=True, text=True)
    assert proc.returncode == 0, f"build failed:\n{proc.stderr[-3000:]}"
    moved = _move_aside(SSH_BINARIES + FIXTURE_ROOTS)
    try:
        yield binary
    finally:
        for root in FIXTURE_ROOTS:
            shutil.rmtree(root, ignore_errors=True)
        _restore(moved)
        shutil.rmtree(build, ignore_errors=True)


def _materialise(files):
    for root in FIXTURE_ROOTS:
        shutil.rmtree(root, ignore_errors=True)
    os.makedirs(SSH_DIR, mode=0o700)
    for rel, content in files.items():
        path = rel if rel.startswith("/") else os.path.join(SSH_DIR, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        os.chmod(path, 0o644)


def _run(binary, case):
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/root",
           "USER": "root", "LOGNAME": "root", "LC_ALL": "C"}
    env.update(case.get("env", {}))
    _materialise(case["files"])
    proc = subprocess.run([binary, *case["args"]], capture_output=True, text=True,
                          env=env, stdin=subprocess.DEVNULL, cwd="/tmp", timeout=30)
    return proc.returncode, proc.stdout


def _check(binary, *groups):
    failures = []
    total = 0
    for group in groups:
        for case in GROUPS[group]:
            total += 1
            rc, out = _run(binary, case)
            if (rc, out) == (case["rc"], case["stdout"]):
                continue
            diff = "".join(difflib.unified_diff(
                case["stdout"].splitlines(True), out.splitlines(True),
                "ssh -G", "hopcfg", n=1))
            failures.append(f"[{group}] args={case['args']} expected rc={case['rc']} "
                            f"got rc={rc}\n{diff}")
    assert total > 0
    assert not failures, (f"{len(failures)}/{total} cases differ from ssh -G:\n"
                          + "\n".join(failures[:4]))


def test_host_line_patterns(hopcfg):
    """Host lines: wildcards, case-sensitive raw-name matching, negated patterns anywhere on the line."""
    _check(hopcfg, "host_patterns")


def test_match_criteria(hopcfg):
    """Match host/originalhost/user/localuser/canonical/all criteria, incl. HostName-based host matching."""
    _check(hopcfg, "match_criteria")


def test_final_pass(hopcfg):
    """Match final triggers a second pass that matches Host/Match against the resolved host name."""
    _check(hopcfg, "final_pass")


def test_include_scoping(hopcfg):
    """Include inside Host/Match blocks, globbed file order and the active state around each included file."""
    _check(hopcfg, "include_scoping")


def test_include_paths(hopcfg):
    """Relative, absolute and ~ Include paths resolve to the same files ssh reads."""
    _check(hopcfg, "include_paths")


def test_precedence_and_lists(hopcfg):
    """Precedence: first obtained value wins across -o/-l/-p/destination/config; lists (IdentityFile, forwards, known hosts) accumulate and dedupe like ssh."""
    _check(hopcfg, "first_value_wins", "list_keywords")


def test_sendenv_setenv(hopcfg):
    """SendEnv accumulation and -pattern removal, SetEnv first-line-wins semantics."""
    _check(hopcfg, "sendenv_setenv")


def test_time_values(hopcfg):
    """Time values with compound units, none, ControlPersist forms and keep-alive defaults and aliases."""
    _check(hopcfg, "time_values")


def test_proxy_settings(hopcfg):
    """ProxyJump/ProxyCommand interplay, jump host formatting and jump host loop rejection."""
    _check(hopcfg, "proxy_settings")


def test_token_expansion(hopcfg):
    """HostName %h expansion and normalisation plus %-token, ${ENV} and ~ expansion in path keywords."""
    _check(hopcfg, "token_expansion")


def test_syntax_and_rejections(hopcfg):
    """Keyword/value spelling variants print like ssh, and invalid configs or destinations exit 255 with no output."""
    _check(hopcfg, "value_formats", "rejected_configs")
