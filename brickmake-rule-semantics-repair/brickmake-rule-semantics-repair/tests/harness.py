"""Plays a build scenario in a scratch directory and records what the build tool printed."""

import os
import shutil
import subprocess
import tempfile

STAMPS = {"old": 1577836800, "mid": 1609459200, "new": 1640995200}
ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/nonexistent", "LC_ALL": "C", "LANG": "C"}


def listing(root):
    out = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            out.append(os.path.relpath(os.path.join(dirpath, f), root))
    return sorted(out)


def play(steps, argv0, normalize=lambda s: s):
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
                    os.remove(os.path.join(work, rel))
            elif kind == "run":
                r = subprocess.run(
                    [*argv0, *step[1:]], cwd=work, env=ENV, capture_output=True, text=True, timeout=60
                )
                results.append({"stdout": normalize(r.stdout), "stderr": normalize(r.stderr), "code": r.returncode})
            elif kind == "ls":
                results.append({"files": listing(work)})
            else:
                raise ValueError(f"unknown step {kind}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return results
