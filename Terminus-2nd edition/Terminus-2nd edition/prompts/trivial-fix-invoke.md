# TRIVIAL / EASY fix invoke (LOCKED)

**When:** Platform label **TRIVIAL**, **EASY — requires at least MEDIUM**, either benchmark **≥3/5**, or worst model **>60%**.

**User does not need to @-tag this file.** Hook + `shared/trivial-first-upload-lock.mdc` auto-route here when summary matches.

**Agent:** If user message is vague (`Fix task`, `harden`, `@trivial` only) → **one question** pointing to Section 1 below. Do **not** edit until slug + platform summary exist.

---

## 1. User copy-paste (fill every bracket)

```text
tasks/<slug>/

Platform rejection — TRIVIAL / EASY. Case 6 structural harden only.

Load in order (do not skip):
@prompts/trivial-fix-invoke.md
shared/trivial-fix-invoke-mandatory-steps.mdc
@prompts/trivial.md
@prompts/trivial-case-6.md
@prompts/sp-hard-create-revise.md
@REVISE RULES
shared/trivial-first-upload-lock.mdc

Platform summary (paste complete — do not paraphrase):
Difficulty: [TRIVIAL | EASY - Requires at least MEDIUM]
Status: [Solvable | Unsolvable]
Agent Performance:
  • terminus-claude-opus-4-8: [X]% ([p]/5 runs)
  • terminus-gpt5-5: [Y]% ([p]/5 runs)
Reference Agents:
  • oracle: [1.0 | 0]
  • nop: [0.0 | 1]

Unit Tests Results (paste every row):
  • test_<name>: [passed]/[runs] runs
  …

Agent must (14 steps — `shared/trivial-fix-invoke-mandatory-steps.mdc`):
1. Quote 2–3 summary facts; router = trivial-fix-invoke → Case 6 (one line why).
2. `Read` invoke + trio + trivial-repo-wide + trivial-hardening-probes.mdc.
3. Write **Section 3 fix prompt** in reply — **before any file edit** (Step 5 hard gate).
4. Inspect real files under tasks/<slug>/ or pending/<slug>/ — list tree; no merge.
3. Harden with interaction depth (not decorative fields):
   - ingest → staging artifact on disk + pytest contract test
   - decoy module NOT on export hot path
   - export-only bugs; ingest-only fix must still fail hidden/replay
   - ≥2 hidden traps independent of bundled root cause
   - persistence / cross-run gate if ledger or sequence exists
4. Forbidden: Case 4/5 only; new hash/fingerprint on same bugs; instruction fix recipes;
   difficulty relabel; weaken tests; TERMINUS_FIRST_SUBMIT_SKIP / TERMINUS_AGENT_CALIBRATION_SKIP
   unless I say so in this message.
5. Run gates before zip (**automatic** — hook runs `./scripts/trivial_easy_auto_finish.sh <slug>` on save + prompt):
   python3 scripts/terminus_auto_probes.py --task-dir tasks/<slug>
   python3 scripts/preupload_agent_calibration.py --record --task-dir tasks/<slug> --opus [p]/5 --gpt [p]/5
6. Finish pipeline (**automatic** — same script; do not use --skip flags):
   ./scripts/trivial_easy_auto_finish.sh <slug>
7. Reply with probe table (revise/trivial-hardening-probes.mdc) + oracle/NOP evidence + zip path.

Target: worst model ≤60% (MEDIUM minimum); aim ≤20% (HARD). Fair + solvable — no 0% forever on one unfair test.
```

---

## 2. Bad vs good (user message)

| Bad — agent will under-fix | Good — agent must follow |
|----------------------------|---------------------------|
| Fix task | Full block above with **slug** + **verbatim platform summary** + **per-test table** |
| Harden it | Names **Case 6 only**, forbidden moves, **probe table** before zip |
| Make it harder | **Structural** changes (staging/decoy/export split), not “add 4 tests” |
| @trivial | `tasks/<slug>/` + summary — tag is hint only |

---

## 3. Agent-written fix prompt (mandatory before edits)

After user pastes Section 1 (or hook injects equivalent summary), agent **writes this block in the reply** then executes it. Replace bracketed fields from the real task — **no generic “fix bugs”**.

```text
## Fix prompt — tasks/<slug>/ (Case 6)

Facts: [Difficulty label]; Opus [p]/5 ([X]%); GPT [p]/5 ([Y]%); worst=[max]%; status=[solvable].
Weakest tests (from platform table): [test_a @ n/10], [test_b @ n/10], …
Router: trivial.md Step B → Case 6 because [EASY label | ≥3/5 | worst >60% | both 5/5].

Structural plan (interaction — not decorative):
1. [e.g. Add /app/state/rollup-snapshot.json written at ingest; test_*snapshot* vs reference]
2. [e.g. Keep merge/apply.go broken decoy; export_stage.go owns publish math]
3. [e.g. Hidden TB3 fixture: wrong merge order passes bundled, fails hidden spread_minutes]
4. [e.g. Cross-run: sequence bumps only after successful export; replay test fails if persistence wrong]

Files to touch (inspect first): [list 5+ modules from real tree — not guessed].

Forbidden this revision: Case 4/5 only; extra JSON fields on same pipeline; instruction leaks.

Done when:
- terminus_auto_probes.py exit 0
- preupload_agent_calibration.py --record shows worst ≤60% OR user accepts defer upload
- create_finish_to_zip.sh <slug> → tasksubmit/<slug>.zip
- Probe table pasted; oracle 1.0 / NOP 0.0 evidence or “not verified yet — WSL harbor”
```

---

## 4. Automation (hooks — no user reminder)

| Trigger | Agent behavior |
|---------|----------------|
| `tasks/<slug>/` + TRIVIAL/EASY summary | **14 mandatory steps** — steps **8–14 AUTO** via `trivial_easy_auto_finish.sh` on prompt + save |
| Vague “fix task” only | One ask: paste Section 1 |
| Summary without slug | One ask: which `tasks/<slug>/` or `pending/<slug>/` |
| Probes PASS but agents >60% | **Do not upload** — deepen per Section 3; record calibration |

---

## Related

- **`shared/trivial-fix-invoke-mandatory-steps.mdc`** — **14-step order (LOCKED)**
- `revise/trivial-easy-difficulty-prompt-lock.mdc`
- `shared/trivial-first-upload-lock.mdc`
- `prompts/trivial.md` · `prompts/trivial-case-6.md` · `prompts/sp-hard-create-revise.md`
