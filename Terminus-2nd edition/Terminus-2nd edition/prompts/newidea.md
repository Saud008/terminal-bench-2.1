# Terminus — Task idea intake (ASK FIRST)

> **LOCKED** — On `gen ideas` / `@prompts/newidea.md`: **ask user** for language, domain, and their idea. **Do not** auto-generate idea lists. Policy: `.cursor/rules/engines/ENGINE_1_ideas.mdc`.

---

## LOCKED — first message = ASK ONLY

If the user says **gen ideas**, **generate ideas**, **brainstorm**, or `@prompts/newidea.md` **without** giving language + domain + their idea:

**Stop. Do not generate anything.** Reply with **one** ask:

```text
Before any ideas or task work, I need three things from you:

1. Primary language — e.g. Rust, Go, Bash, Java, TypeScript
2. Domain — industry or scenario (your pick, not mine)
3. Your task idea — 1–3 sentences: what should the agent fix or build?

I will not invent a batch of ideas. After you reply, I will scan tasks/, pending/, _accepted-tasks/, and tasksubmit/ for similarity only.
```

**Forbidden on first turn:** 10/25 idea lists · invented domains · `jobs-local/ideas-draft.json` filled with agent titles · `@CREATE` / new `tasks/<name>/`.

---

## After user gives language + domain + idea

### 1. Corpus scan (mandatory)

```bash
ls tasks/
ls pending/ 2>/dev/null
ls tasks/_accepted-tasks/
ls tasksubmit/*.zip 2>/dev/null
```

### 2. Similarity gate (mandatory script — do not guess)

```bash
python3 scripts/idea_similarity_gate.py \
  --language "<lang>" \
  --domain "<domain>" \
  --title "<short title>" \
  --summary "<user idea>"
```

Read **`jobs-local/idea-similarity-gate-last.json`**.

| Weighted sim | Verdict | Action |
|--------------|---------|--------|
| **> 0.10** | **BLOCK** | Nearest neighbor + change domain — **no CREATE** |
| **== 0.0** | **PASS + AUTO_CREATE** | Start `@CREATE` Phase A **immediately** — no “build it” |
| **0 < sim ≤ 0.10** | **PASS** | User confirms → then CREATE |

Family: ≤2 same family in `tasks/` for that lane (script may also block).

Hook: `jobs-local/anti-spam-hook-last.txt` when `ideas-draft.json` saved.

### 3. Reply shape (similarity turn)

```markdown
## Corpus check
- tasks/: N · pending/: N · _accepted-tasks/: N · zips: N

## Your idea (from you)
- Language: …
- Domain: …
- Idea: …

## Similarity
- Nearest: tasks/<slug>/ (from `idea-similarity-gate-last.json`)
- Weighted sim: … (scripted — not guessed)
- Verdict: BLOCKED (>0.10) | PASS auto CREATE (==0) | PASS confirm build (0–0.10)
- Structural diffs (if PASS build): 1. … 2. …

## Next step
- BLOCKED (>0.10): change domain or shape — I will not create.
- sim == 0: starting @CREATE Phase A now (no build confirmation needed).
- 0 < sim ≤ 0.10: say **build it** if you want me to implement.
```

**Do not** output Mode A batch templates or 25+5 lists unless user explicitly asks for a **batch** after a PASS.

---

## Batch / deep spec (only if user explicitly asks later)

If user says e.g. "give 5 alternatives" or "full deep spec" **after** intake — use single Mode B block for **one** idea only. Each alternative still needs similarity PASS before build.

---

## After user says build / implement (or AUTO_CREATE when sim == 0)

`@CREATE RULES` → one `tasks/<new-unique-name>/` → Phase E auto audit → F → F′ → `./scripts/pack_zip.sh <name>` when ready.

**AUTO_CREATE (sim == 0):** skip waiting for “build it” — enter CREATE in the **same** turn after gate PASS.

---

## Invoke

```text
gen ideas
```

```text
@prompts/newidea.md
Language: Go. Domain: hospital lab instrument calibration. Idea: CLI replays serial frames and exports a audit JSON but checksum and sequence bugs break replay.
```

Second form → similarity turn only, not generation.
