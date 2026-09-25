# Fixture catalog

Bundled scenarios under /app/fixtures/scenarios/:

| Name | Focus |
|------|-------|
| 001-atime-btime-age | max(atime,btime) age gate |
| 002-exclude-depth | eN exclude depth pruning |
| 003-recreate-after-age | z waits for subtree age cleanup |
| 004-ownership-before-remove | ownership before destructive remove |
| 005-boot-ex-merge | generator boot vs boot-ex |
| 006-nested-glob | globstar nested candidates |
| 007-combined-trap | interacting age, exclude, recreate |
| 008-ownership-survivor | ownership on path that survives remove |

Each scenario includes tree.json and rules.conf except 005 which uses fragments/ for generate tests.
