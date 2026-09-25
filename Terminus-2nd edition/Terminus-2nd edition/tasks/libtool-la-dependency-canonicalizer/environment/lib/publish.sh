#!/usr/bin/env bash
# Manifest publish — broken builds re-walk .la files instead of the staged snapshot.

lt_publish_manifest() {
  local out="$1"
  lt_validate_snapshot || return 1
  local work
  work="$(mktemp -d)"
  local project="${LT_ROOT:-}"
  if [ -z "${project}" ] && [ -f /app/state/lt-scan-snapshot.json ]; then
    project="$(python3 -c 'import json;print(json.load(open("/app/state/lt-scan-snapshot.json"))["project_root"])')"
  fi
  [ -n "${project}" ] || return 1

  lt_graph_load "${project}" "${work}" || return 2
  lt_break_cycles

  TOTAL_RPATH_DEDUP=0
  LIBS_FILE="${work}/libs.ndjson"
  : > "${LIBS_FILE}"
  : > "${work}/broken.ndjson"

  for id in "${LT_IDS[@]}"; do
    lt_resolve_dir "${id}"
    lt_merge_names "${id}"
    lt_installed_flag "${id}"
    lt_linkorder_deps "${id}"
    lt_dedupe_rpath "${id}"
    TOTAL_RPATH_DEDUP=$((TOTAL_RPATH_DEDUP + LT_RPATH_DEDUP_REMOVED))

    la_relpath=""
    for la_path in "${LT_LA_PATHS[@]}"; do
      if [ "$(basename "${la_path}" .la)" = "${id}" ]; then
        la_relpath="${la_path#"${project}/"}"
        break
      fi
    done
    la_relpath="${la_relpath//\\//}"

    deps_file="${work}/${id}.deps"
    rpath_file="${work}/${id}.rpath"
    printf '%s\n' "${LT_LINKORDER_RESULT[@]}" > "${deps_file}"
    printf '%s\n' "${LT_RPATH_RESULT[@]}" > "${rpath_file}"

    export LT_ROW_ID="${id}"
    export LT_ROW_REL="${la_relpath}"
    export LT_ROW_RESOLVE="${LT_RESOLVE_DIR}"
    export LT_ROW_INSTALLED="${LT_INSTALLED}"
    export LT_ROW_SHARED="${LT_SHARED_NAME}"
    export LT_ROW_STATIC="${LT_STATIC_FALLBACK}"
    export LT_ROW_DEPS_FILE="${deps_file}"
    export LT_ROW_RPATH_FILE="${rpath_file}"
    export LT_LIBS_FILE="${LIBS_FILE}"

    python3 - <<'PY'
import json, os, pathlib
deps = [l.strip() for l in pathlib.Path(os.environ["LT_ROW_DEPS_FILE"]).read_text(encoding="utf-8").splitlines() if l.strip()]
rpath = [l.strip() for l in pathlib.Path(os.environ["LT_ROW_RPATH_FILE"]).read_text(encoding="utf-8").splitlines() if l.strip()]
row = {
    "id": os.environ["LT_ROW_ID"],
    "la_relpath": os.environ["LT_ROW_REL"],
    "installed": os.environ["LT_ROW_INSTALLED"] == "true",
    "resolve_dir": os.environ["LT_ROW_RESOLVE"],
    "dependency_order": deps,
    "rpath": rpath,
    "shared_name": os.environ["LT_ROW_SHARED"],
    "static_fallback": os.environ["LT_ROW_STATIC"],
}
with open(os.environ["LT_LIBS_FILE"], "a", encoding="utf-8") as f:
    f.write(json.dumps(row) + "\n")
PY
  done

  for edge in "${LT_BROKEN[@]:-}"; do
    [ -z "${edge}" ] && continue
    from="${edge%%/*}"
    to="${edge#*/}"
    python3 - <<PY
import json, pathlib
row={"from":"${from}","to":"${to}"}
with open("${work}/broken.ndjson","a",encoding="utf-8") as f:
    f.write(json.dumps(row)+"\n")
PY
  done

  export LT_MANIFEST_OUT="${out}"
  export LT_MANIFEST_PROJECT="${project}"
  export LT_MANIFEST_LIBS="${LIBS_FILE}"
  export LT_MANIFEST_BROKEN="${work}/broken.ndjson"
  export LT_MANIFEST_RPATH_DEDUP="${TOTAL_RPATH_DEDUP}"

  python3 - <<'PY'
import json, os, pathlib
libs = []
for line in pathlib.Path(os.environ["LT_MANIFEST_LIBS"]).read_text(encoding="utf-8").splitlines():
    if line.strip():
        libs.append(json.loads(line))
broken = []
for line in pathlib.Path(os.environ["LT_MANIFEST_BROKEN"]).read_text(encoding="utf-8").splitlines():
    if line.strip():
        broken.append(json.loads(line))
manifest = {
    "manifest_version": 1,
    "project_root": os.environ["LT_MANIFEST_PROJECT"],
    "stats": {
        "la_files": len(libs),
        "cycles_broken": len(broken),
        "rpaths_deduped": int(os.environ["LT_MANIFEST_RPATH_DEDUP"]),
    },
    "libraries": sorted(libs, key=lambda x: x["id"]),
    "broken_edges": broken,
}
out = pathlib.Path(os.environ["LT_MANIFEST_OUT"])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY
}
