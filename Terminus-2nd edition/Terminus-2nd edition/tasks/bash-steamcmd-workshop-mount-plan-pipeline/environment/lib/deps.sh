#!/usr/bin/env bash
# Dependency admission and required-edge graph builder.
#
# BROKEN: semver constraints are compared as ASCII strings, so numeric
# versions like 1.10.0 sort below 1.2.0 and fail >=1.2.0 spuriously.
#
# Sets:
#   DEPS_ERRORS      array of contract-formatted error strings
#   DEPS_EDGE_COUNT  count of admitted edges
# Writes admitted edges (dependency\tdependent\toptional) to DEPS_GRAPH_FILE.

deps_build_graph() {
  local staged_tsv="$1"
  local errfile
  errfile="$(mktemp)"
  DEPS_EDGE_COUNT="$(python3 - "${staged_tsv}" "${DEPS_GRAPH_FILE}" "${errfile}" "${PLAN_INCLUDE_OPTIONAL:-1}" <<'PY'
import sys

staged, graph_path, err_path, inc_opt = sys.argv[1:5]
include_optional = inc_opt == "1"

mods = {}
deps = []
with open(staged, encoding="utf-8") as fh:
    for raw in fh:
        line = raw.rstrip("\n")
        if not line:
            continue
        parts = line.split("\t")
        if parts[0] == "MOD":
            mid = parts[1] if len(parts) > 1 else ""
            ver = parts[2] if len(parts) > 2 else ""
            mods[mid] = ver
        elif parts[0] == "DEP":
            frm = parts[1] if len(parts) > 1 else ""
            to = parts[2] if len(parts) > 2 else ""
            constraint = parts[3] if len(parts) > 3 else ""
            optional = parts[4] if len(parts) > 4 else "0"
            deps.append((frm, to, constraint, optional))


def parse_constraint(c):
    for op in (">=", "<=", "==", ">", "<"):
        if c.startswith(op):
            return op, c[len(op):].strip()
    return ">=", c.strip()


def semver_ok(have, constraint):
    # BROKEN: ASCII string comparison instead of numeric semver.
    op, want = parse_constraint(constraint)
    if op == ">=":
        return have >= want
    if op == ">":
        return have > want
    if op == "<=":
        return have <= want
    if op == "<":
        return have < want
    if op == "==":
        return have == want
    return have >= want


edges = []
errors = []
edge_count = 0
for frm, to, constraint, optional in deps:
    is_opt = optional == "1"
    if is_opt and not include_optional:
        continue
    if to not in mods:
        if is_opt:
            continue
        errors.append("missing required dependency: %s -> %s (%s)" % (frm, to, constraint))
        continue
    have = mods[to]
    if not semver_ok(have, constraint):
        errors.append("semver constraint failed: %s requires %s %s (have %s)" % (frm, to, constraint, have))
        continue
    edges.append((to, frm, "1" if is_opt else "0"))
    edge_count += 1

with open(graph_path, "w", encoding="utf-8") as gh:
    for a, b, o in edges:
        gh.write("%s\t%s\t%s\n" % (a, b, o))
with open(err_path, "w", encoding="utf-8") as eh:
    for e in errors:
        eh.write(e + "\n")
print(edge_count)
PY
)"
  DEPS_ERRORS=()
  if [[ -s "${errfile}" ]]; then
    mapfile -t DEPS_ERRORS < "${errfile}"
  fi
  rm -f "${errfile}"
}
