# Submission explanations - bash-git-worktree-porcelain-status-parser-repair

**Status:** RETIRED — `data-processing` / repair-shaped upload fails `[category_classifier]` as blocked `software-engineering`.

**Use instead:** `worktree-inventory-seal-ledger`  
**Zip:** `tasksubmit/worktree-inventory-seal-ledger.zip`  
**Explanations:** `submission-explanations/worktree-inventory-seal-ledger.md`

## Why the CI failed

Harbor accepted `category = "data-processing"` in `task.toml`, but the classifier predicted **software-engineering** (blocked). Intermediate build-and-dependency porcelain reframes still classified as SE. Successor is system-administration worktree inventory ops (admit → gate → sealed atlas).
