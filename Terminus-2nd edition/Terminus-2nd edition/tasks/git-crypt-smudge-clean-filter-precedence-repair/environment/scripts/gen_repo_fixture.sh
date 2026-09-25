#!/usr/bin/env bash
set -euo pipefail

seed=""
output=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --seed)
      seed="$2"
      shift 2
      ;;
    --output)
      output="$2"
      shift 2
      ;;
    *)
      echo "usage: gen_repo_fixture.sh --seed SEED --output ROOT" >&2
      exit 2
      ;;
  esac
done

[[ -n "$seed" && -n "$output" ]] || {
  echo "usage: gen_repo_fixture.sh --seed SEED --output ROOT" >&2
  exit 2
}

mkdir -p "$output/.gcrypt/keys"
python3 - "$seed" "$output" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

seed, out = sys.argv[1], Path(sys.argv[2])
digest = hashlib.sha256(seed.encode()).hexdigest()
key_id = digest[:8]
material = digest[8:40] + digest[:24]
(out / ".gcrypt/keys/default").write_text(
    f"key_id={key_id}\nmaterial={material}\n", encoding="utf-8"
)
attrs = """# generated seed repo
secret/** filter=gcrypt
!secret/public.txt -filter
*.overlay filter=gcrypt
public/** -filter
"""
(out / ".gitattributes").write_text(attrs, encoding="utf-8")
(out / "secret").mkdir(parents=True, exist_ok=True)
(out / "public").mkdir(parents=True, exist_ok=True)
(out / "secret" / "seed.bin").write_bytes(os.urandom(16))
(out / "secret" / "public.txt").write_text("must stay plaintext\n", encoding="utf-8")
(out / "public" / "note.txt").write_text("public\n", encoding="utf-8")
(out / "vault.overlay").write_text("overlay\n", encoding="utf-8")
PY
