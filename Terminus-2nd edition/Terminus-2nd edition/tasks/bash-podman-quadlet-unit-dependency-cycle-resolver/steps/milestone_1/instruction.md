The `quadlet-resolver` driver under `/app/bin` walks Podman Quadlet `.container` trees and emits merged unit metadata, but parse output from `/app/fixtures/` does not match `/app/docs/quadlet-format.md`. Milestone 1 covers **parse and drop-in merge only**.

Repair `/app/lib/parse.sh`. The surface parser at `/app/tools/quadlet_parser.py` tokenizes each fragment; do not replace it. Follow `/app/docs/quadlet-format.md` and `/app/docs/cli-reference.md`. Do not edit `/app/docs/` or `/app/fixtures/`.

```text
quadlet-resolver parse --tree /app/fixtures/stack --out /app/output/parse.json
```
