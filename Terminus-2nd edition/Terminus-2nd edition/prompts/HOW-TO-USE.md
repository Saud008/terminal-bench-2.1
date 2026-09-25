# How to use prompts — **you choose**

**You never need to say “analyze” or “use prompt”** — paste summary + task name; agent does it automatically every chat.

Two equal paths. Pick whichever you prefer each time.

---

## Path 1 — @ tag one prompt

Type **`@`** → pick **one** tag → paste summary.

| Tag | When |
|-----|------|
| `@TRIVIAL PROMPT` | TRIVIAL / EASY |
| `@MEDIUM PROMPT` | MEDIUM |
| `@HARD PROMPT` | HARD / not solvable |
| `@REVIEWER PROMPT` | Reviewer comments |
| `@AUDIT PROMPT` | Post-create audit |
| `@ORACLE PROMPT` | Oracle failed only |
| `@NEWIDEA PROMPT` | Ideas |
| `@PROMPTS` | Index |

```text
@HARD PROMPT

Fix tasks/<task-name>

Platform summary:
[paste here]
```

Your tag = **hint only**. Agent **always analyzes summary first**, applies prompt **matching the summary**, auto-picks best case. Wrong tag → overridden (you don't repeat this).

---

## Path 2 — Automated (no tag)

Paste only task path + summary. Hook + rules route for you.

**Platform summary** should include **Agent Performance** for `terminus-claude-opus-4-8` and `terminus-gpt5-5` (not legacy Opus 4.6 / GPT-5.2). See [`LOCKED.md`](LOCKED.md) § Benchmark agents.

```text
Fix tasks/<task-name>

Platform summary:
[paste here]
```

Same result: agent analyzes → picks router + case → reads `prompts/*.md` → fixes task.

**@ tag help:** see this file only — `prompts/CURSOR-AT-TAG.md` was removed (duplicate of § below).

---

## Both paths — agent always

1. Quote 2–3 facts from summary  
2. Pick router + best case (summary wins over wrong tag)  
3. `Read` full prompt files from `prompts/`  
4. Oracle **1**, NOP **0** → `./scripts/pack_zip.sh <name>`  

Missing summary → **one question**, no guessing.

---

## Can't @ tag? — **you're fine without it**

**Path 2 (summary only) is complete.** You do not need tags for routing to work.

### If you still want to tag

`prompts/trivial.md` files often **do not** appear in Cursor's `@` menu. Use **Rules**, not Files:

1. In chat, type **`@`**
2. Open the **Rules** section (not Files)
3. Search: `TRIVIAL PROMPT`, `HARD PROMPT`, `REVIEWER PROMPT`, etc.
4. Or search: `@PROMPTS` for the index

**Do not** type `@prompts/trivial.md` — that path usually won't show.

### If Rules don't appear

- Restart Cursor (rules load on open)
- Confirm this folder is the workspace root: `Terminus-2nd edition`
- Check **Cursor Settings → Rules** — project rules enabled
- **Skip tagging** — paste summary only; hook + `prompt-router` handle everything

### What to paste (no tag)

```text
Fix tasks/<task-name>

Platform summary:
[paste everything from platform]
```

That is enough. Every time.
