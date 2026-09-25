# Submission explanations — bash-podman-quadlet-unit-dependency-cycle-resolver

**Task folder:** tasks/bash-podman-quadlet-unit-dependency-cycle-resolver/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This three-milestone task is medium difficulty because the quadlet-resolver bash driver must keep parse merge, DAG ordering, and systemd emission aligned across four /app/docs contracts while each milestone gates the next. Milestone 1 drop-in merge is easy to get wrong when After= is applied before Wants= from a later fragment, or when list keys like EnvironmentFile do not accumulate in basename-sorted drop-in order. Milestone 2 builds directed edges from After= and Wants= only, so agents often invent false cycles or sort by timestamp instead of Kahn with lexicographic tie-break among ready units. Milestone 3 render must take Restart= from [Service] while ignoring [Container] Restart=, synthesize ExecStart from Image=, and abort without writing files when a cycle is detected. Seed-derived synthetic unit names in pytest catch hard-coded parse or order logic that passes the bundled stack alone.

## Solution Explanation

The oracle copies corrected parse.sh, dag.sh, and emit.sh into /app/lib for the final milestone, with earlier milestones patching only the module under test. Parse walks each .container tree, calls the surface quadlet_parser.py once per base and drop-in fragment, merges Wants, Requires, and EnvironmentFile in phase one, then merges After= in phase two, and writes parse.json. Order runs parse internally, builds dependency edges where each After= or Wants= target must precede its unit, detects cycles with a DFS report on stderr as cycle:unit1,unit2,..., and emits topological order JSON using Kahn with lexicographic ready-queue selection. Render invokes order first, then writes one .service per unit under the output directory with merged [Unit] keys, Service EnvironmentFile and Restart lines, synthesized podman ExecStart, and WantedBy=multi-user.target in dependency order.

## Verification Explanation

Twenty-one pytest functions across three milestones drive quadlet-resolver parse, order, and render through subprocess on fresh output paths. Each milestone ships reference_quadlet.py to independently merge fragments, build edges, detect cycles, compute topological order, and render expected unit files, so answers cannot be copied from bundled JSON. Milestone 1 asserts eight-unit stack parse, drop-in lexicographic merge, parser touch logging, and seed-injected trees. Milestone 2 checks reference order match, edge validity, db-before-redis tie-break, Wants-only non-cycles, built-in and seed-injected cycle exit 2, and proxy-before-frontend constraints. Milestone 3 compares rendered units to the reference, verifies EnvironmentFile and Restart policy, runs systemd-analyze verify on every emitted file, rejects render output on cycles, and confirms fixtures are not mutated.
