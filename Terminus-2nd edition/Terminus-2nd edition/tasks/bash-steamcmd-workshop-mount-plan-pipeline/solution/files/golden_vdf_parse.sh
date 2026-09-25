#!/usr/bin/env bash
# Parse a Steam Workshop VDF manifest into declaration-ordered TSV rows.
#
# Emits:
#   MOD\t{mod_id}\t{version}
#   DEP\t{from_mod}\t{to_mod}\t{constraint}\t{optional}
# where from_mod is the dependent and to_mod is the dependency target.

vdf_parse_manifest() {
  local manifest_file="$1"
  python3 - "${manifest_file}" <<'PY'
import sys


def tokenize(text):
    toks = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "{":
            toks.append(("open", "{"))
            i += 1
        elif c == "}":
            toks.append(("close", "}"))
            i += 1
        elif c == '"':
            i += 1
            buf = []
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    buf.append(text[i + 1])
                    i += 2
                else:
                    buf.append(text[i])
                    i += 1
            i += 1
            toks.append(("str", "".join(buf)))
        else:
            start = i
            while i < n and text[i] not in ' \t\r\n{}"':
                i += 1
            toks.append(("str", text[start:i]))
    return toks


def parse_block(toks, i):
    items = []
    while i < len(toks):
        t, v = toks[i]
        if t == "close":
            return items, i + 1
        key = v
        i += 1
        if i >= len(toks):
            break
        nt, nv = toks[i]
        if nt == "open":
            block, i = parse_block(toks, i + 1)
            items.append((key, block))
        else:
            items.append((key, nv))
            i += 1
    return items, i


def find_block(items, name):
    for k, v in items:
        if k == name and isinstance(v, list):
            return v
    return None


def emit(text):
    toks = tokenize(text)
    root, _ = parse_block(toks, 0)
    coll = None
    for _k, v in root:
        if isinstance(v, list):
            coll = v
            break
    lines = []
    if coll is None:
        return lines
    mods = find_block(coll, "mods")
    if mods is None:
        return lines
    for mod_id, mod_body in mods:
        if not isinstance(mod_body, list):
            continue
        version = ""
        depends = None
        for k, v in mod_body:
            if k == "version" and isinstance(v, str):
                version = v
            elif k == "depends" and isinstance(v, list):
                depends = v
        lines.append("MOD\t%s\t%s" % (mod_id, version))
        if depends:
            for dep_id, dep_body in depends:
                if not isinstance(dep_body, list):
                    continue
                constraint = ""
                optional = "0"
                for k, v in dep_body:
                    if k == "version" and isinstance(v, str):
                        constraint = v
                    elif k == "optional" and isinstance(v, str):
                        optional = v
                lines.append("DEP\t%s\t%s\t%s\t%s" % (mod_id, dep_id, constraint, optional))
    return lines


text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
for line in emit(text):
    print(line)
PY
}
