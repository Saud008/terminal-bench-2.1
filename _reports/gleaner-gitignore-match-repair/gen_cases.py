#!/usr/bin/env python3
"""Record expected gleaner output from real git for every spec case.

usage: gen_cases.py OUT_JSON [GLEANER_BINARY ...]
Each extra binary is run against the recorded cases and a per-group pass/fail table is printed.
"""
import json
import os
import random
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import specs  # noqa: E402

BASE, HOME, XDG = specs.BASE, specs.HOME, specs.XDG
REPO = BASE + "/repo"

NAMES = ["a", "b", "ab", "a-b", "a.b", "x.o", "foo", "bar", "build", "doc", "log", "A", "abc", "a b",
         "#c", "!n", "a*b", "[x]", "1", "z0", "a0", "keep", "foo.txt", "b.log", "ba", "a ", "x", "a]b", "-"]
DIRNAMES = ["a", "b", "build", "doc", "sub", "foo", "a-b", "x", "log", "deep", "A", "ab", "a.b"]
ATOMS = ["a", "b", "ab", "foo", "bar", "build", "doc", "log", "x", "keep", "sub", "deep", "o", "txt",
         "*", "*", "**", "?", "[a-c]", "[!a]", "[^a]", "[]a]", "[!]a]", "[[:digit:]]", "[[:alpha:]]",
         "\\*", "\\!", "\\#", "\\ ", ".", "-", "***", "[a-]", "[:a]", "\\[x]"]


def rand_pattern(rng):
    pat = "/".join("".join(rng.choice(ATOMS) for _ in range(rng.randint(1, 3))) for _ in range(rng.randint(1, 3)))
    r = rng.random()
    if r < 0.2:
        pat = "/" + pat
    elif r < 0.3:
        pat = "**/" + pat
    if rng.random() < 0.25:
        pat += "/"
    if rng.random() < 0.1:
        pat += "/**"
    if rng.random() < 0.25:
        pat = "!" + pat
    elif rng.random() < 0.05:
        pat = "\\!" + pat
    r = rng.random()
    if r < 0.1:
        pat += "  "
    elif r < 0.15:
        pat += "\\ "
    elif r < 0.2:
        pat += "\t"
    return pat


def rand_text(rng, pool):
    lines = []
    for _ in range(rng.randint(2, 8)):
        r = rng.random()
        if r < 0.1:
            lines.append("")
        elif r < 0.17:
            lines.append("# " + rng.choice(pool))
        elif r < 0.5:
            lines.append(rng.choice(["", "!", "/", "**/"]) + rng.choice(pool) + rng.choice(["", "", "/"]))
        else:
            lines.append(rand_pattern(rng))
    eol = "\r\n" if rng.random() < 0.15 else "\n"
    text = eol.join(lines) + (eol if rng.random() < 0.8 else "")
    return ("\ufeff" + text) if rng.random() < 0.1 else text


def mixed_cases(seed, count):
    rng = random.Random(seed)
    out = []
    for n in range(count):
        dirs = [""]
        for _ in range(rng.randint(2, 8)):
            parent = rng.choice(dirs)
            if parent.count("/") >= 2:
                continue
            d = (parent + "/" if parent else "") + rng.choice(DIRNAMES)
            if d not in dirs:
                dirs.append(d)
        files = {}
        for d in dirs:
            for _ in range(rng.randint(1, 5)):
                p = (d + "/" if d else "") + rng.choice(NAMES)
                if p not in dirs and not any(x.startswith(p + "/") for x in dirs):
                    files[p] = "x\n"
        pool = NAMES + DIRNAMES
        for d in dirs:
            if rng.random() < 0.6:
                files[(d + "/" if d else "") + ".gitignore"] = rand_text(rng, pool)
        c = {"name": f"mixed_{n:02d}", "files": files}
        if rng.random() < 0.5:
            c["exclude"] = rand_text(rng, pool)
        r = rng.random()
        if r < 0.3:
            c["config"] = specs.DEFAULT_CONFIG + "\t" + rng.choice(["excludesFile", "excludesfile"]) + " = ~/gi\n"
            c["home"] = {"gi": rand_text(rng, pool)}
        elif r < 0.5:
            c["env"] = {"XDG_CONFIG_HOME": XDG}
            c["xdg"] = {"git/ignore": rand_text(rng, pool)}
        elif r < 0.7:
            c["home"] = {".config/git/ignore": rand_text(rng, pool)}
        paths = sorted(set(d for d in dirs if d) | set(files))
        c["checks"] = rng.sample(paths, min(len(paths), 14))
        out.append(c)
    return out


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def materialize(c, with_git):
    for p in c["files"]:
        assert not any(q.startswith(p + "/") for q in c["files"]), (c["name"], "file is also a dir", p)
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(REPO)
    os.makedirs(HOME)
    if with_git:
        subprocess.run(["git", "init", "-q", REPO], check=True, env=env_for(c))
        shutil.rmtree(REPO + "/.git/hooks")
        os.remove(REPO + "/.git/info/exclude")
    else:
        os.makedirs(REPO + "/.git/info")
    write(REPO + "/.git/config", c.get("config", specs.DEFAULT_CONFIG))
    if "exclude" in c:
        write(REPO + "/.git/info/exclude", c["exclude"])
    for p, t in c["files"].items():
        write(os.path.join(REPO, p), t)
    for p, t in c.get("home", {}).items():
        write(os.path.join(HOME, p), t)
    for p, t in c.get("xdg", {}).items():
        write(os.path.join(XDG, p), t)


def env_for(c):
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": HOME, "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1"}
    env.update(c.get("env", {}))
    return env


def run(cmd, c):
    p = subprocess.run(cmd, cwd=REPO, env=env_for(c), capture_output=True)
    return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")


def record(c):
    materialize(c, True)
    rc, out, err = run(["git", "ls-files", "--others", "--exclude-standard"], c)
    assert rc == 0 and not err, (c["name"], err)
    assert '"' not in out, (c["name"], "git quoted a path", out)
    c["list"] = out
    rc, chk, err = run(["git", "check-ignore", "-v", "-n", "--"] + c["checks"], c)
    assert not err and rc in (0, 1), (c["name"], err)
    lines = chk.splitlines()
    assert len(lines) == len(c["checks"]), (c["name"], chk)
    ignored = False
    for line in lines:
        left = line.split("\t", 1)[0]
        if left != "::":
            ignored |= not left.split(":", 2)[2].startswith("!")
    c["check"] = chk
    c["check_rc"] = 0 if ignored else 1


def compare(binary, c):
    materialize(c, False)
    rc, out, err = run([binary, "list"], c)
    if rc != 0 or out != c["list"]:
        return f"list rc={rc} {err.strip()}"
    rc, out, err = run([binary, "check", "--"] + c["checks"], c)
    if rc != c["check_rc"] or out != c["check"]:
        return f"check rc={rc} (want {c['check_rc']})"
    return None


def main():
    out_json = sys.argv[1]
    groups = dict(specs.G)
    groups["mixed_trees"] = mixed_cases(20260927, 30)
    for name, cases in groups.items():
        for c in cases:
            record(c)
    for binary in sys.argv[2:]:
        print(f"== {binary}")
        for name, cases in groups.items():
            fails = [(c["name"], why) for c in cases if (why := compare(binary, c))]
            print(f"  {'FAIL' if fails else 'pass'} {name}: {len(fails)}/{len(cases)} " + "; ".join(f"{n}: {w}" for n, w in fails[:3]))
    keep = ("name", "files", "config", "exclude", "home", "xdg", "env", "checks", "list", "check", "check_rc")
    data = {"groups": {g: [{k: c[k] for k in keep if k in c} for c in cases] for g, cases in groups.items()}}
    with open(out_json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=True)
        f.write("\n")
    print("wrote", out_json, sum(len(v) for v in groups.values()), "cases")


if __name__ == "__main__":
    main()
