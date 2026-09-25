Bundle files use the .bundle extension. Each file declares one bundle.

Lines are space-separated tokens. Comments start with #.

bundle NAME declares the bundle identifier.

service NAME TYPE declares a service. TYPE is oneshot or longrun.

dep CHILD hard PARENT declares a hard dependency: CHILD must start after PARENT is up.

dep CHILD soft PARENT or soft dep CHILD soft PARENT declares a soft dependency used for export closure only; soft edges do not affect topological start order.

longrun NAME marks a longrun service that participates in the ready barrier described in /app/docs/ready-barrier.md.

Ingest output is JSON with tree, bundles map, and per-bundle services, hard_deps, soft_deps, and longruns arrays matching the parser in /app/tools/bundle_parser.py.
