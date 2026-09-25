# Submission explanations - dgraph-predicate-upsert-conflict-repair

**Status:** RETIRED — old Go/`data-processing` upload fails `[category_classifier]` as blocked `software-engineering`.

**Use instead:** `predattest-mutation-conflict-attest-ledger`  
**Zip:** `tasksubmit/predattest-mutation-conflict-attest-ledger.zip`  
**Explanations:** `submission-explanations/predattest-mutation-conflict-attest-ledger.md`

## Why the CI failed

Harbor accepted `category = "data-processing"` in `task.toml`, but the classifier predicted **software-engineering** (blocked). Metadata alone cannot fix that — the task had to be reframed as fleet-ops / system-administration (wavehold hold-preview), which is the predattest successor.
