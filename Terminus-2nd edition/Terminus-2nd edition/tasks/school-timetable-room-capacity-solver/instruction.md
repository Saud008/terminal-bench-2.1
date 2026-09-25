District registrar operators need a host-local timetable allocation control plane that keeps roster admission, constraint-graph materialization, room and lab capacity gates, teacher conflict barriers, split-section cohort locks, allocation-pass seals, and sealed timetable-atlas publish aligned across offline roster windows. Operate ttalloc under /app so load, materialize, allocate, and publish follow the ops contracts in /app/docs/registrar-cli.md, /app/docs/roster-bundle-contract.md, /app/docs/constraint-graph-contract.md, /app/docs/split-section-contract.md, /app/docs/teacher-conflict-contract.md, /app/docs/room-capacity-contract.md, /app/docs/lab-room-contract.md, /app/docs/stable-score-contract.md, /app/docs/allocation-pass-contract.md, /app/docs/timetable-atlas-contract.md, /app/docs/conflict-report-contract.md, and /app/docs/verifier-refmath-contract.md.

ttalloc load-roster --scenario NAME [--fixture-dir PATH] must copy the admitted roster bundle into /app/state/active-roster.json and record scenario metadata at /app/state/scenario-active.json.

ttalloc materialize-graph --scenario NAME must write /app/state/constraint-graph.json and must emit lab_requirement edges whenever requires_lab is true.

ttalloc allocate-slots --scenario NAME must write /app/work/allocate-log.json and advance allocation_pass stored in /app/state/allocation-pass.json.

ttalloc publish-atlas --scenario NAME must emit /app/output/timetable-atlas.json and /app/output/conflict-report.json only when allocation_pass is greater than zero. Fixed verb order is defined in /app/docs/registrar-cli.md.

Non-empty split_group values force identical slot_id across cohort sections. Lab courses require room_kind lab. Combined enrolled per room and slot must respect capacity minus policies.capacity_margin. Each teacher_id may appear once per slot_id. Final atlas rank precedence follows /app/docs/stable-score-contract.md lexicographic tie rules.

Binary path: /app/bin/ttalloc. Bundled scenarios live under /app/fixtures. Hidden verifier fixtures may supply alternate directories under /opt/verifier-fixtures/ttalloc. Do not edit /app/docs/ or /app/fixtures/.
