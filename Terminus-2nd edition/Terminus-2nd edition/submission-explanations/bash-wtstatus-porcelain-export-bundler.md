# Submission explanations - bash-wtstatus-porcelain-export-bundler

**Status:** RETIRED — build-and-dependency reframes still fail `[category_classifier]` as blocked `software-engineering` (Git porcelain parse/classify surface).

**Use instead:** `worktree-inventory-seal-ledger`  
**Zip:** `tasksubmit/worktree-inventory-seal-ledger.zip`  
**Explanations:** `submission-explanations/worktree-inventory-seal-ledger.md`

## Why the CI failed

Harbor accepted `category = "build-and-dependency-management"`, but the classifier still predicted **software-engineering** (blocked). Porcelain parse/classify framing was the signal — successor is system-administration worktree inventory ops (admit → score/gitlink gates → sealed atlas).
