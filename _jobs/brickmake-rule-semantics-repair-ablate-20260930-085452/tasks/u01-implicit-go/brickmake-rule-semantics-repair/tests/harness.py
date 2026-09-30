"""Builds brickmake from the agent's /app as an unprivileged user and plays build
scenarios with it in scratch directories, recording what it printed."""

import os
import resource
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

GO = "/usr/local/go/bin/go"
SANDBOX = Path("/tmp/sandbox")
BINARY = SANDBOX / "bin" / "brickmake"
USER, GROUP = "nobody", "nogroup"
STAMPS = {"old": 1577836800, "mid": 1609459200, "new": 1640995200}
BUILD_ENV = {
    "PATH": "/usr/local/go/bin:/usr/bin:/bin",
    "HOME": str(SANDBOX / "home"),
    "GOCACHE": str(SANDBOX / "gocache"),
    "GOPATH": str(SANDBOX / "gopath"),
    "GOTOOLCHAIN": "local",
    "GOPROXY": "off",
    "GOFLAGS": "-buildvcs=false",
    "CGO_ENABLED": "0",
    "LANG": "C",
}
RUN_ENV = {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LC_ALL": "C", "LANG": "C"}


def _limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 30, 1 << 30))
    resource.setrlimit(resource.RLIMIT_NPROC, (4096, 4096))


def sandboxed(argv, cwd, env, timeout):
    """Run argv as nobody with resource limits, a fixed environment and its own
    process group, which is killed afterwards whatever happened."""
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        user=USER,
        group=GROUP,
        extra_groups=[],
        preexec_fn=_limits,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        raise AssertionError(f"{argv[0]} did not finish within {timeout}s\nstdout:\n{out}\nstderr:\n{err}") from None
    finally:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return proc.returncode, out, err


def build():
    """Compile /app/cmd/brickmake with the standard library only and return the binary path."""
    for sub in ("home", "gocache", "gopath", "bin"):
        (SANDBOX / sub).mkdir(parents=True, exist_ok=True)
        shutil.chown(SANDBOX / sub, USER, GROUP)
    if BINARY.exists():
        BINARY.unlink()
    code, out, err = sandboxed([GO, "build", "-o", str(BINARY), "./cmd/brickmake"], "/app", BUILD_ENV, 600)
    assert code == 0, f"go build ./cmd/brickmake failed:\n{out}{err}"
    code, out, err = sandboxed([GO, "list", "-m"], "/app", BUILD_ENV, 120)
    assert code == 0, f"go list -m failed:\n{out}{err}"
    module = out.strip()
    code, out, err = sandboxed(
        [GO, "list", "-deps", "-f", "{{if not .Standard}}{{.ImportPath}}{{end}}", "./cmd/brickmake"],
        "/app", BUILD_ENV, 300)
    assert code == 0, f"go list -deps ./cmd/brickmake failed:\n{out}{err}"
    foreign = [p for p in out.split() if p != module and not p.startswith(module + "/")]
    assert not foreign, f"brickmake must use the Go standard library only, found: {foreign}"
    return str(BINARY)


def _chown_tree(root):
    shutil.chown(root, USER, GROUP)
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            shutil.chown(os.path.join(dirpath, name), USER, GROUP)


def listing(root):
    out = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            out.append(os.path.relpath(os.path.join(dirpath, f), root))
    return sorted(out)


def play(steps, binary):
    """Apply write/touch/rm steps, run the binary for each run step and record
    stdout, stderr and exit status; ls records the files left on disk."""
    work = tempfile.mkdtemp(prefix="bm-")
    results = []
    try:
        for step in steps:
            kind = step[0]
            if kind == "write":
                path = os.path.join(work, step[1])
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(step[2])
            elif kind == "touch":
                when = STAMPS[step[1]]
                for rel in step[2:]:
                    path = os.path.join(work, rel)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    open(path, "a", encoding="utf-8").close()
                    os.utime(path, (when, when))
            elif kind == "rm":
                for rel in step[1:]:
                    path = os.path.join(work, rel)
                    assert os.path.exists(path), f"{rel} should have been built before this step removes it"
                    os.remove(path)
            elif kind == "run":
                _chown_tree(work)
                code, out, err = sandboxed([binary, *step[1:]], work, RUN_ENV, 60)
                results.append({"stdout": out, "stderr": err, "code": code})
            elif kind == "ls":
                results.append({"files": listing(work)})
            else:
                raise ValueError(f"unknown step {kind}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return results
