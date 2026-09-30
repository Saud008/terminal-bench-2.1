"""Compose solution/solve.sh from correct-src for every file that differs from environment/app/src."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "gleaner-gitignore-match-repair" / "gleaner-gitignore-match-repair"
SRC = TASK / "environment" / "app" / "src"
GOOD = HERE / "correct-src"

NOTES = {
    "ignore/lines.rs": "Skip a leading byte order mark, drop the CR of CRLF line ends, and number lines as they are in the file.",
    "ignore/parse.rs": "Trim only unescaped trailing spaces, leave a leading backslash to the matcher, and strip the trailing slash before deciding whether the pattern has a slash.",
    "ignore/pattern.rs": "Slash patterns are relative to the directory of the .gitignore they come from.",
    "ignore/wildmatch.rs": "A run of stars only crosses directories when it is a whole component, and `**/` may also match no directory.",
    "ignore/charclass.rs": "`[^...]` negates like `[!...]`, and a `]` right after the opening bracket is a member.",
    "ignore/stack.rs": "Deeper .gitignore files win, and a negation can't rescue anything inside an excluded directory.",
    "ignore/sources.rs": ".git/info/exclude outranks the excludes file.",
    "config/paths.rs": "The default excludes file lives under XDG_CONFIG_HOME when that is set and not empty.",
    "config/gitconfig.rs": "Config key names are case-insensitive.",
    "walk/order.rs": "git ls-files order is plain byte order of the whole path.",
}

parts = ["#!/usr/bin/env bash", "set -euo pipefail", "", "cd /app", ""]
for rel in sorted(NOTES, key=lambda r: list(NOTES).index(r)):
    good = (GOOD / rel).read_text(encoding="utf-8")
    cur = (SRC / rel).read_text(encoding="utf-8")
    assert good != cur, rel
    assert "\nRUST\n" not in good
    parts.append(f"# {NOTES[rel]}")
    parts.append(f"cat > /app/src/{rel} <<'RUST'")
    parts.append(good.rstrip("\n"))
    parts.append("RUST")
    parts.append("")
for p in sorted(GOOD.rglob("*.rs")):
    rel = p.relative_to(GOOD).as_posix()
    if rel not in NOTES:
        assert p.read_text(encoding="utf-8") == (SRC / rel).read_text(encoding="utf-8"), f"unlisted diff {rel}"
parts.append("cargo build --release --offline")
out = TASK / "solution" / "solve.sh"
out.write_bytes(("\n".join(parts) + "\n").encode("utf-8"))
print("wrote", out, len(NOTES), "files")
