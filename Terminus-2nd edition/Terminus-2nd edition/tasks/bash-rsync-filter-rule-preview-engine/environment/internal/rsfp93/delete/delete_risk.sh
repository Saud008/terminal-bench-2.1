        #!/usr/bin/env bash
        set -euo pipefail

        classify_delete_risk() {
          local path="$1"
          local transfer="$2"
          local token="$3"
          local receiver_json="$4"
          python3 - <<'PY' "$path" "$transfer" "$token" "$receiver_json"
import json, sys
path, transfer, token, receiver_json = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
receiver = set(json.loads(receiver_json))
if path in receiver and transfer == "exclude":
    print("candidate")
else:
    print("none")
PY
        }
