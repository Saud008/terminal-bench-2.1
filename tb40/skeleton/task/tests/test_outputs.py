"""<<REPLACE: what this suite validates>>"""

import os
import resource
import shutil
import signal
import subprocess
from pathlib import Path

APP = Path("/app")
GO = "/usr/local/go/bin/go"
SANDBOX = Path("/tmp/sandbox")
SANDBOX_USER = "nobody"
SANDBOX_GROUP = "nogroup"
SANDBOX_ENV = {
    "PATH": "/usr/local/go/bin:/usr/bin:/bin",
    "HOME": str(SANDBOX / "home"),
    "GOCACHE": str(SANDBOX / "gocache"),
    "GOPATH": str(SANDBOX / "gopath"),
    "GOTOOLCHAIN": "local",
    "GOPROXY": "off",
    "GOFLAGS": "-buildvcs=false",
    "LANG": "C.UTF-8",
}


def _limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 30, 1 << 30))
    resource.setrlimit(resource.RLIMIT_NPROC, (4096, 4096))


def run_sandboxed(argv: list[str], cwd: Path, timeout: int = 300, stdin: str | None = None) -> subprocess.CompletedProcess:
    """Run agent-produced code as an unprivileged, resource-bounded process with a clean env."""
    for sub in ("home", "gocache", "gopath", "bin"):
        (SANDBOX / sub).mkdir(parents=True, exist_ok=True)
        shutil.chown(SANDBOX / sub, SANDBOX_USER, SANDBOX_GROUP)
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=SANDBOX_ENV,
        user=SANDBOX_USER,
        group=SANDBOX_GROUP,
        extra_groups=[],
        preexec_fn=_limits,
        start_new_session=True,
        stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        out, err = proc.communicate(input=stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        raise AssertionError(f"{argv[0]} did not finish within {timeout}s\nstdout:\n{out}\nstderr:\n{err}") from None
    finally:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return subprocess.CompletedProcess(argv, proc.returncode, out, err)


def build_app() -> Path:
    binary = SANDBOX / "bin" / "app"
    result = run_sandboxed([GO, "build", "-o", str(binary), "."], cwd=APP)
    assert result.returncode == 0, f"go build failed:\n{result.stderr}"
    return binary


def test_replace_me():
    """<<REPLACE: the behavior this test verifies>>"""
    binary = build_app()
    result = run_sandboxed([str(binary)], cwd=APP)
    assert result.returncode == 0, f"expected exit 0, got {result.returncode}: {result.stderr}"
