# Terminus tasks (source)

Active task bundles live here — one folder per task, matching `Default_Task_Skeleton` layout:

```
tasks/<task-name>/
  instruction.md
  task.toml
  environment/
  solution/solve.sh
  tests/test.sh
  tests/test_outputs.py
```

**Do not** put `node_modules/`, `dist/`, or local `jobs/` in git or submission zips.

**Local Harbor** (macOS Desktop — use an external jobs dir):

```bash
harbor run -a oracle -p "/path/to/Terminus-2nd edition/tasks/<task-name>" \
  -o "$HOME/Terminus/harbor-jobs"
```

Build submission zips into **`tasksubmit/`** in this repo (see `tasksubmit/README.md`). For the lock-free ringbuffer task: `python3 scripts/build-lock-free-ringbuffer-zip.py`.
