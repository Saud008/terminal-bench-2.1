# .cursor/hooks — Terminus automation

Rebuild ENGINE bundles after editing `archive/terminus-rules-mdc/`:

```bash
python3 scripts/build_consolidated_rules.py
python3 scripts/terminus_engine_healthcheck.py
```

**Restart Cursor** after any hook change.

## hooks.json

| Hook | Script | When |
|------|--------|------|
| `beforeSubmitPrompt` | `route-terminus-prompt.py` | Every prompt — inject ENGINE bundle + route + run paste pipelines |
| `postToolUse` / `afterFileEdit` (Write) | `anti-spam-auto-run.py` | Save under `tasks/<slug>/` or `pending/<slug>/` |

## Paste → agent turn (`beforeSubmitPrompt`)

| Paste type | Auto |
|------------|------|
| **CREATE / task path** | ENGINE_3 + standing requirements |
| **TRIVIAL/EASY summary** | Save `jobs-local/calibration/trivial-easy-context-<slug>.json` · inject 14-step block · **no finish until save** |
| **Reviewer comments** | Save `jobs-local/calibration/reviewer-feedback-context-<slug>.json` · run `reviewer_feedback_gate.py` · **audit + gate only** until save |
| **Ideas** | `idea_similarity_gate` when `jobs-local/ideas-draft.json` exists |

## Save → pipeline (`afterFileEdit` / `postToolUse`)

Debounced **45s** per slug. Order:

1. `post_create_audit_loop.py` (static audit)
2. `unacceptable_class_gate.py` (8/8)
3. `reviewer_feedback_gate.py` — **only if** reviewer context exists
4. Finish:
   - TRIVIAL context → `trivial_easy_auto_finish.py` (probes + finish)
   - else → `create_finish_to_zip.py` → `pack_zip.sh`

Reports: `jobs-local/anti-spam-hook-last.txt` · `jobs-local/finish/create-finish-last.json`

## pack_zip.sh (automatic inside finish)

Gate order (all must pass; **similarity must be 0.0**):

1. Canonical ECR `FROM`
2. `subcategories = []` · allowed `category`
3. Anti-spam / templated (`PACK_SIM_MUST_BE_ZERO`)
4. Unacceptable-class 8/8
5. First-submit F′
6. Agent calibration (HARD ≤20%)
7. Difficulty design gate
8. Trivial shape S1–S7
9. `terminus_ci_check.py`
10. Zip + `terminus_verify_submit.py` (G-025–G-027)

Override flags exist (`TERMINUS_*_SKIP`) — **user explicit only**.

## Manual debug (optional)

```bash
python3 scripts/terminus_preflight.py --task-dir tasks/<name>
python3 scripts/reviewer_feedback_gate.py --task-dir tasks/<name> --context
python3 scripts/create_finish_to_zip.sh <name>
./scripts/pack_zip.sh <name>
```
