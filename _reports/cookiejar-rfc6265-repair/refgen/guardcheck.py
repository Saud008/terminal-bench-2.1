"""Exercises the source-policy guard of tests/test_outputs.py on sample snippets and scans trajectories for grading paths."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "cookiejar-rfc6265-repair"
src = (TASK / "cookiejar-rfc6265-repair" / "tests" / "test_outputs.py").read_text(encoding="utf-8")
ns: dict = {"__file__": str(TASK / "cookiejar-rfc6265-repair" / "tests" / "test_outputs.py")}
exec(src.split("@pytest.fixture")[0].replace("import pytest", ""), ns)
strip, forb = ns["_strip_comments"], ns["FORBIDDEN_CODE"]

samples = {
    "comment mentions Command::new and unsafe": "// never use std::process::Command::new or unsafe here\nfn f() {}",
    "block comment mentions extern": "/* extern \"C\" is not allowed */ fn f() {}",
    "identifier unsafe_count": "let unsafe_count = 1;",
    "real Command::new": "fn f() { std::process::Command::new(\"true\"); }",
    "use std::process::{Command}": "use std::process::{Stdio, Command};",
    "real unsafe block": "fn f() { unsafe { } }",
}
for name, code in samples.items():
    hits = [k for k, p in forb.items() if p.search(strip(code))]
    print(f"{name:40s} -> {hits or 'clean'}")

pat = re.compile(r"/tests/|test_outputs\.py|ctrf\.json|reward\.txt|/logs/verifier|/solution/")
for run in sorted((TASK / "trajectories").glob("run-0*")):
    t = (run / "agent" / "trajectory.json").read_text(encoding="utf-8")
    print(run.name, sorted(set(pat.findall(t))))
sys.exit(0)
