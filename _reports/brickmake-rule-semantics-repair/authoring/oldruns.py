"""Show which test groups each archived TB 2.1 model run failed."""

import json
import pathlib

root = pathlib.Path("brickmake-rule-semantics-repair/trajectories")
for run in sorted(root.glob("run-0*")):
    tests = json.loads((run / "verifier" / "ctrf.json").read_text(encoding="utf-8"))["results"]["tests"]
    failed = [t["name"].split("::")[-1].removeprefix("test_") for t in tests if t["status"] != "passed"]
    print(run.name, "FAILED:", failed or "none")
