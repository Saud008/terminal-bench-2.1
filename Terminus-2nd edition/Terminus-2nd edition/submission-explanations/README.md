# Submission explanations (platform upload form)

One file per task slug — **not** included in `tasksubmit/*.zip`.

| File | Platform fields |
|------|-----------------|
| `submission-explanations/<slug>.md` | Difficulty · Solution · Verification (copy-paste on submit) |

Write with:

```bash
python3 scripts/write_submission_explanations.py --slug <name> --draft
python3 scripts/submission_explanations_gate.py --check --slug <name>
```

Edit the draft in your own words before uploading. Pack is blocked until the gate passes.
