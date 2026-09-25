# Inventory ops workflow

This task is a **system-administration** host-local wtstatus-export worktree inventory ops control plane. Operators admit offline depot inventory stream fixtures into an isolated run, enforce rename-score admission gates and gitlink hold barriers, and publish sealed inventory atlases from gated state only. The working baseline under /app must keep admission gates, hold barriers, and sealed atlas export aligned; it is not a generic service repair exercise.

## Stages

1. Admit a NUL-delimited inventory stream from --porcelain.
2. Gate rename and copy rows with rename_score_min from export config.
3. Apply gitlink hold when any mode field equals 160000.
4. Publish sealed atlas JSON at --export with stable path order and summary counts.
