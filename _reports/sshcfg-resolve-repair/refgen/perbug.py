"""Apply each planted bug alone to the correct tree and count failing cases."""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, "/w")
import harness  # noqa: E402
from cases_src import GROUPS  # noqa: E402

BUGS = {
    "B1 host negation": ("readconf.c",
        "if (match_pattern(host, arg)) {\n\t\t\t\tif (negated) {\n\t\t\t\t\t*activep = 0;\n\t\t\t\t\targv_consume(&ac);\n\t\t\t\t\tbreak;\n\t\t\t\t}\n\t\t\t\t*activep = 1;\n\t\t\t}",
        "if (match_pattern(host, arg))\n\t\t\t\t*activep = !negated;"),
    "B2 match host target": ("matchcfg.c",
        "\telse if (options->hostname != NULL)\n\t\ttarget = percent_expand(options->hostname, keys);\n",
        ""),
    "B3 include restore": ("readconf.c",
        "\t\t\t\t*activep = oactive;\n\t\t\t\tif (r != 1)\n\t\t\t\t\tvalue = -1;\n\t\t\t}\n",
        "\t\t\t\tif (r != 1)\n\t\t\t\t\tvalue = -1;\n\t\t\t}\n\t\t\t*activep = oactive;\n"),
    "B5 include relative": ("readconf.c",
        '(flags & CONF_USER) ?\n\t\t\t\t    "~/.ssh" : "/etc/ssh", arg);',
        '(flags & CONF_USER) ?\n\t\t\t\t    "." : "/etc/ssh", arg);'),
    "B6 final host": ("main.c",
        "process_config_files(host, options.host_arg, 1, NULL);",
        "process_config_files(options.host_arg, options.host_arg, 1, NULL);"),
    "B7 convtime": ("convtime.c", "total += secs;", "total = secs;"),
    "B8 sendenv removal": ("strlist.c", "match_pattern(l->v[i], pattern)",
        "match_pattern(pattern, l->v[i])"),
    "B9 setenv": ("readconf.c", "if (!*activep || value != 0)", "if (!*activep)"),
    "B10 proxyjump": ("jump.c",
        "active &= o->proxy_command == NULL && o->jump_host == NULL;",
        "active &= o->jump_host == NULL;"),
    "B11 batchmode": ("options.c", "o->batch_mode == 1 ? 300 : 0", "0"),
    "B12 silent": ("dump.c", '"SILENT", "FATAL"', '"QUIET", "FATAL"'),
    "B13 keyalias": ("main.c", "options.host_key_alias : options.host_arg;",
        "options.host_key_alias : host;"),
}


def main():
    cases = [(g, c) for g, cs in GROUPS.items() for c in cs]
    expected = []
    for g, c in cases:
        rc, out = harness.run(["ssh", "-G"], c)
        expected.append((rc, harness.filter_ssh(out) if rc == 0 else ""))
    for name, (fname, old, new) in BUGS.items():
        shutil.rmtree("/t", ignore_errors=True)
        shutil.copytree("/good", "/t")
        path = os.path.join("/t/src", fname)
        src = open(path).read()
        if old not in src:
            print(f"{name}: PATTERN NOT FOUND")
            continue
        open(path, "w").write(src.replace(old, new, 1))
        subprocess.run(["make", "-s", "-C", "/t", "CFLAGS=-std=c11 -O2 -w"],
                       check=True, capture_output=True)
        hits = {}
        for (g, c), exp in zip(cases, expected):
            if harness.run(["/t/hopcfg"], c) != exp:
                hits[g] = hits.get(g, 0) + 1
        print(f"{name}: {hits}")


if __name__ == "__main__":
    main()
