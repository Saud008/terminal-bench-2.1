"""Per-defect ablation inside the task image: fixed tree + one defect re-planted."""
import shutil
import subprocess
from pathlib import Path

SRC = Path("/app/src")
FIXED = {p.name: p.read_text() for p in SRC.glob("*.c")}

DEFECTS = {
    "origin_resets_owner": ("directives.c", "    ctx->origin = origin;\n}\n\nstatic void do_ttl",
                            "    ctx->origin = origin;\n    ctx->owner = origin;\n    ctx->have_owner = 1;\n}\n\nstatic void do_ttl"),
    "include_keeps_ttl": ("directives.c", "    ctx->ttl = saved_ttl;\n", ""),
    "include_path_strchr": ("directives.c", "strrchr(including", "strchr(including"),
    "ttl_precedence": ("ttl.c",
                       "    if (c->has_dollar) {\n        *out = c->dollar;\n        return 1;\n    }\n    if (c->has_last) {\n        *out = c->last;\n        return 1;\n    }\n",
                       "    if (c->has_last) {\n        *out = c->last;\n        return 1;\n    }\n    if (c->has_dollar) {\n        *out = c->dollar;\n        return 1;\n    }\n"),
    "lexer_parens_in_quotes": ("lexer.c", None, None),
    "escape_case_fold": ("name.c", "    out->len = wl;\n    name_lower(out);\n", "    out->len = wl;\n"),
    "label_length_text": ("name.c",
                          "            if (lablen == LABEL_MAX) {\n                *err = \"label too long\";\n                return -1;\n            }\n",
                          ""),
    "sort_by_text": ("zone.c", "name_cmp_canonical(&a->owner, &b->owner)", "strcmp(a->owner_text, b->owner_text)"),
    "digest_before_ttls": ("zone.c", "    z->n = out;\n\n    for", "    z->n = out;\n\n    zonemd_update(z);\n\n    for"),
    "zonemd_excludes_all": ("zonemd.c", "        if (is_apex_zonemd(z, &z->v[i]))\n            continue;\n        hash_rr",
                            "        if (z->v[i].type == TYPE_ZONEMD)\n            continue;\n        hash_rr"),
    "zonemd_serial": ("zonemd.c", "buf_put32(&rd, z->soa_serial);", "buf_put32(&rd, rd_get32(md->rd));"),
    "sha_padding": ("sha384.c", "buflen > 112", "buflen > 120"),
    "rrset_min_ttl": ("zone.c", "            if (z->v[j].seq < z->v[first].seq)\n                first = j;\n",
                      "            if (z->v[j].ttl < z->v[first].ttl)\n                first = j;\n"),
}

INQ = """            if (inq) {
                if (c == '"') {
                    push(ll, &cur, 1);
                    inq = 0;
                } else {
                    buf_put8(&cur, (unsigned char)c);
                }
                continue;
            }
"""
PAREN_START = "            if (c == '(' || c == ')') {"
PAREN_END = "                    fail_at(&pos, \"unbalanced parentheses\");\n                continue;\n            }\n"

for name, (fname, old, new) in DEFECTS.items():
    for f, text in FIXED.items():
        (SRC / f).write_text(text)
    text = FIXED[fname]
    if name == "lexer_parens_in_quotes":
        assert INQ in text
        text = text.replace(INQ, "", 1)
        end = text.index(PAREN_END, text.index(PAREN_START)) + len(PAREN_END)
        text = text[:end] + INQ + text[end:]
    else:
        assert text.count(old) == 1, (name, old)
        text = text.replace(old, new)
    if name == "digest_before_ttls":
        assert text.count("    }\n\n    zonemd_update(z);\n}") == 1
        text = text.replace("    }\n\n    zonemd_update(z);\n}", "    }\n}")
    if name == "label_length_text":
        text = text.replace("        w[lenpos] = (unsigned char)lablen;",
                            "        if (lablen > LABEL_MAX) {\n            *err = \"label too long\";\n            return -1;\n        }\n"
                            "        w[lenpos] = (unsigned char)lablen;").replace(
            "        int lablen = 0;\n", "        int lablen = 0;\n        const char *start = p;\n").replace(
            "if (lablen > LABEL_MAX)", "if (p - start > LABEL_MAX)")
    (SRC / fname).write_text(text)
    shutil.rmtree("/tmp/zonec-verify-build", ignore_errors=True)
    r = subprocess.run(["/opt/pytools/bin/python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        "/tests/test_outputs.py", "-rf"], capture_output=True, text=True)
    failed = [l.split("::")[1].split(" ")[0] for l in r.stdout.splitlines() if l.startswith("FAILED")]
    print(f"{name:26s} failing: {', '.join(failed) or 'NONE'}")

for f, text in FIXED.items():
    (SRC / f).write_text(text)
