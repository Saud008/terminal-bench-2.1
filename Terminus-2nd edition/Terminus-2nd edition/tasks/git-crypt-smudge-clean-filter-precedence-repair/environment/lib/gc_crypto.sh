#!/usr/bin/env bash
# Encrypt/decrypt blobs and HMAC helpers.

# shellcheck source=gc_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/gc_common.sh"
# shellcheck source=gc_keys.sh
source "$(dirname "${BASH_SOURCE[0]}")/gc_keys.sh"

gc_crypto_encrypt_file() {
  local repo="$1"
  local src_file="$2"
  gc_key_load "$repo" || return 1
  python3 - "$GC_KEY_ID" "$GC_KEY_MATERIAL" "$src_file" <<'PY'
import base64
import hashlib
import sys
from pathlib import Path

key_id, material_hex, src = sys.argv[1], sys.argv[2], sys.argv[3]
material = bytes.fromhex(material_hex)
data = Path(src).read_bytes()
text = data.decode("utf-8", errors="surrogateescape")
text = text.replace("\r\n", "\n").replace("\r", "\n")
norm = text.encode("utf-8", errors="surrogateescape")
hmac = hashlib.sha256(norm).hexdigest()
out = bytes(b ^ material[i % len(material)] for i, b in enumerate(norm))
b64 = base64.b64encode(out).decode("ascii")
print(f"GCRYPT1\nKEY:{key_id}\nDATA:{b64}\nHMAC:{hmac}")
PY
}

gc_crypto_decrypt_file() {
  local repo="$1"
  local blob_file="$2"
  local out_file="$3"
  local head
  head="$(head -c 7 "$blob_file" 2>/dev/null || true)"
  if [[ "$head" != "GCRYPT1" ]]; then
    cat "$blob_file" > "$out_file"
    return 0
  fi
  gc_key_load "$repo" || return 1
  python3 - "$GC_KEY_ID" "$GC_KEY_MATERIAL" "$blob_file" "$out_file" <<'PY'
import base64
import hashlib
import sys
from pathlib import Path

key_id, material_hex, blob_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
material = bytes.fromhex(material_hex)
blob = Path(blob_path).read_text(encoding="utf-8")
lines = blob.splitlines()
fields = {}
for line in lines:
    if line.startswith("KEY:"):
        fields["key"] = line[4:]
    elif line.startswith("DATA:"):
        fields["data"] = line[5:]
    elif line.startswith("HMAC:"):
        fields["hmac"] = line[5:]
if fields.get("key") != key_id:
    raise SystemExit(1)
raw = bytes(b ^ material[i % len(material)] for i, b in enumerate(base64.b64decode(fields["data"])))
if hashlib.sha256(raw).hexdigest() != fields["hmac"]:
    raise SystemExit(1)
Path(out_path).write_bytes(raw)
PY
}

gc_crypto_clean_filter() {
  local repo="$1"
  local relpath="$2"
  local tmp
  tmp="$(mktemp)"
  gc__stdin_slurp_file "$tmp"
  local blob_tmp
  blob_tmp="$(mktemp)"
  gc_crypto_encrypt_file "$repo" "$tmp" > "$blob_tmp"
  # shellcheck source=gc_attrs.sh
  source "$(dirname "${BASH_SOURCE[0]}")/gc_attrs.sh"
  if gc_attrs_filter_active "$repo" "$relpath"; then
    cat "$blob_tmp"
  else
    cat "$tmp"
  fi
  rm -f "$tmp" "$blob_tmp"
}

gc_crypto_smudge_filter() {
  local repo="$1"
  local relpath="$2"
  local blob_tmp out_tmp
  blob_tmp="$(mktemp)"
  out_tmp="$(mktemp)"
  gc__stdin_slurp_file "$blob_tmp"
  if [[ "$(head -c 7 "$blob_tmp" 2>/dev/null || true)" == "GCRYPT1" ]]; then
    # shellcheck source=gc_attrs.sh
    source "$(dirname "${BASH_SOURCE[0]}")/gc_attrs.sh"
    if ! gc_attrs_filter_active "$repo" "$relpath"; then
      rm -f "$blob_tmp" "$out_tmp"
      return 2
    fi
  fi
  if ! gc_crypto_decrypt_file "$repo" "$blob_tmp" "$out_tmp"; then
    rm -f "$blob_tmp" "$out_tmp"
    return 2
  fi
  cat "$out_tmp"
  rm -f "$blob_tmp" "$out_tmp"
}

gc_pipeline_smudge() {
  local repo="$1"
  local relpath="$2"
  local use_staging="$3"
  local blob_tmp out_tmp
  blob_tmp="$(mktemp)"
  out_tmp="$(mktemp)"
  gc__stdin_slurp_file "$blob_tmp"
  if [[ $use_staging -eq 1 ]]; then
    gc_staging_write "$relpath" ""
  fi
  if ! gc_crypto_decrypt_file "$repo" "$blob_tmp" "$out_tmp"; then
    rm -f "$blob_tmp" "$out_tmp"
    return 2
  fi
  if [[ $use_staging -eq 1 ]]; then
    cp "$blob_tmp" "$(gc_staging_path_for "$relpath")"
  fi
  cat "$out_tmp"
  rm -f "$blob_tmp" "$out_tmp"
}
