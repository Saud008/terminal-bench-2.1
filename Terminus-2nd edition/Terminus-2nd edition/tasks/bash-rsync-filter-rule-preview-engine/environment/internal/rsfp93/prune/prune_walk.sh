        #!/usr/bin/env bash
        set -euo pipefail

        should_prune_directory() {
          local dir_path="$1"
          local transfer="$2"
          local token="$3"
          python3 - <<'PY' "$dir_path" "$transfer" "$token"
import sys
path, transfer, token = sys.argv[1], sys.argv[2], sys.argv[3]
is_dir = "." not in path.split("/")[-1]
if is_dir:
    print("false")
else:
    print("false")
PY
        }
