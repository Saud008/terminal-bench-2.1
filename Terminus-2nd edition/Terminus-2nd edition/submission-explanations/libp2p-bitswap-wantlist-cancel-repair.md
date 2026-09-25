# Submission explanations - libp2p-bitswap-wantlist-cancel-repair

**Status:** RETIRED — forbidden `repair` token; Harbor `[category_classifier]` predicted blocked `software-engineering` under `data-processing` / repair framing.

**Use instead:** `bitswap-wantlist-session-seal-ledger`  
**Zip:** `tasksubmit/bitswap-wantlist-session-seal-ledger.zip`  
**Explanations:** `submission-explanations/bitswap-wantlist-session-seal-ledger.md`

## Why the CI failed

Harbor accepted `category = "data-processing"` in `task.toml`, but the classifier predicted **software-engineering** (blocked). Metadata alone cannot fix that — the task had to be regenerated as a system-administration host-local bitswap session seal ledger (bswapd), which is the successor.
