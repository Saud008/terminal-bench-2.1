"""Assembles solution/solve.sh from the fixed sources in _reports/.../fixed."""
from pathlib import Path

HERE = Path(__file__).parent
FIXED = HERE / "fixed"
OUT = HERE.parent.parent / "pinwheel-semver-range-repair" / "pinwheel-semver-range-repair" / "solution" / "solve.sh"

STEPS = [
    ("internal/semver/version.go", "Numeric prerelease identifiers must not carry leading zeros (1.2.3-01 is invalid)."),
    ("internal/semver/compare.go", "Prerelease precedence: numeric identifiers compare as numbers, and a longer\n# identifier list wins when the shorter one is a prefix of it."),
    ("internal/semrange/comparator.go", "An exact comparator matches on precedence, so build metadata is ignored."),
    ("internal/semrange/range.go", "'||' may have any amount of whitespace around it, and a prerelease is only\n# admitted by a set that names a prerelease of the same major.minor.patch."),
    ("internal/semrange/caret.go", "Caret keeps the left-most non-zero field: ^0.2.3 < 0.3.0-0, ^0.0.3 < 0.0.4-0."),
    ("internal/semrange/tilde.go", "~1 means >=1.0.0 <2.0.0-0, not ~1.0."),
    ("internal/semrange/xrange.go", ">1.2 means >=1.3.0 and <=1.2 means <1.3.0-0."),
    ("internal/semrange/hyphen.go", "A partial upper bound covers everything it matches: 1.2 - 2.3 is <2.4.0-0."),
    ("internal/resolve/resolver.go", "Each round replaces the selection, so packages nobody requires any more drop out."),
    ("internal/resolve/constraints.go", "An override replaces the dependents' ranges instead of being added to them."),
    ("internal/resolve/yanked.go", "A bare full version is an exact pin too, not only '=VERSION'."),
    ("internal/resolve/candidates.go", "Equal-precedence ties go to the latest published release (then file order)\n# whichever way prefer points."),
    ("internal/lockfile/lockfile.go", "pin.lock is written without HTML escaping ('<root>', '>=1.2' stay as-is)."),
]

parts = [
    "#!/usr/bin/env bash",
    "set -euo pipefail",
    "",
    "cd /app",
    "",
]
for rel, why in STEPS:
    body = (FIXED / rel).read_text(encoding="utf-8")
    assert "\nGOSRC\n" not in body
    parts.append(f"# {why}")
    parts.append(f"cat > /app/{rel} <<'GOSRC'")
    parts.append(body.rstrip("\n"))
    parts.append("GOSRC")
    parts.append("")

parts += [
    'test -z "$(gofmt -l .)"',
    "go vet ./...",
    "go test ./...",
    "go build -o /usr/local/bin/pinwheel ./cmd/pinwheel",
    "",
]
OUT.write_bytes("\n".join(parts).encode("utf-8"))
print(OUT, len(parts))
