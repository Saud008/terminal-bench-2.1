"""Run every case through real ssh -G and hopcfg; report differences.

usage: python3 diffcheck.py /path/to/hopcfg [--record out.json]
"""
import json
import sys

sys.path.insert(0, "/w")
import harness  # noqa: E402
from cases_src import GROUPS  # noqa: E402


def main():
    binary = sys.argv[1]
    record = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--record" else None
    quiet = "-q" in sys.argv
    failed = {}
    bad = 0
    total = 0
    recorded = {}
    for name, cases in GROUPS.items():
        recorded[name] = []
        for case in cases:
            total += 1
            src, sout = harness.run(["ssh", "-G"], case)
            exp = harness.filter_ssh(sout) if src == 0 else ""
            hrc, hout = harness.run([binary], case)
            if hrc != 0:
                hout = hout if hout else ""
            recorded[name].append({**case, "rc": src, "stdout": exp})
            if (src, exp) != (hrc, hout):
                bad += 1
                failed.setdefault(name, 0)
                failed[name] += 1
                if not quiet:
                    print(f"### {name} args={case['args']}")
                    print(f"ssh rc={src}\n{exp}hopcfg rc={hrc}\n{hout}")
    print(f"{total - bad}/{total} match")
    for name in GROUPS:
        print(f"  {name}: {failed.get(name, 0)}/{len(GROUPS[name])} differ")
    if record:
        with open(record, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"groups": recorded}, fh, indent=1, sort_keys=False)
            fh.write("\n")


if __name__ == "__main__":
    main()
