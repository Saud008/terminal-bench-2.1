# Pagestore ops workflow

This task is a **system-administration** host-local page-registry ops control plane. Operators admit offline JSONL batch fixtures into an isolated staging lane, enforce registry rebalance gates during apply, run a commit barrier that seals child page payloads before recording root height, then publish sealed export JSON and walk metrics from committed tables only. The working baseline under /app must keep staging admission, commit barriers, and sealed export aligned; it is not a generic service repair exercise.

## Offline pass shape

1. **Admit** - `redbtool batch` writes put/delete lines into staging only.
2. **Gate** - registry rebalance rules in /app/docs/registry-rebalance-rules.md keep the page map consistent as staging mutates.
3. **Barrier** - `redbtool commit` flushes child pages, writes the commit record, publishes committed tables, and writes /app/state/btree-snapshot.json.
4. **Seal** - `redbtool export` and `redbtool walk` read committed state only.

There is no remote cluster. Independent evaluations start from a clean /app/state/ tree via /app/scripts/reset-state.sh.
