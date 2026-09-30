#!/usr/bin/env python3
"""Differential fuzz: gleaner list/check vs git ls-files -o --exclude-standard / check-ignore -v -n."""
import os
import random
import shutil
import subprocess
import sys

GLEANER = sys.argv[1]
N = int(sys.argv[2])
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 1
BASE = "/tmp/fz"
REPO = BASE + "/repo"
HOME = BASE + "/home"
XDG = BASE + "/xdg"

NAMES = ["a", "b", "ab", "a-b", "a.b", "x.o", "foo", "bar", "build", "doc", "log", "A", "abc",
         "a b", "#c", "!n", "a*b", "[x]", "1", "z0", "a0", "keep", "foo.txt", "b.log", "ba", "a ",
         "sub", "x", "a]b", "-", "a\\b"]
NAMES = [n for n in NAMES if "\\" not in n]
DIRNAMES = ["a", "b", "build", "doc", "sub", "foo", "a-b", "x", "log", "deep", "A", "ab"]

ATOMS = ["a", "b", "ab", "foo", "bar", "build", "doc", "log", "x", "keep", "sub", "deep", "o", "txt",
         "*", "*", "**", "?", "[a-c]", "[!a]", "[^a]", "[]a]", "[!]a]", "[[:digit:]]", "[[:alpha:]]",
         "\\*", "\\!", "\\#", "\\ ", ".", "-", "***", "[a-]", "[[:bogus:]]", "[:a]", "\\[x]", "[x"]


def rand_pattern(rng):
    parts = []
    for _ in range(rng.randint(1, 3)):
        comp = "".join(rng.choice(ATOMS) for _ in range(rng.randint(1, 3)))
        parts.append(comp)
    pat = "/".join(parts)
    r = rng.random()
    if r < 0.2:
        pat = "/" + pat
    elif r < 0.3:
        pat = "**/" + pat
    if rng.random() < 0.25:
        pat = pat + "/"
    if rng.random() < 0.1:
        pat = pat + "/**"
    if rng.random() < 0.25:
        pat = "!" + pat
    elif rng.random() < 0.05:
        pat = "\\!" + pat
    elif rng.random() < 0.05:
        pat = "\\#" + pat
    r = rng.random()
    if r < 0.1:
        pat += "  "
    elif r < 0.15:
        pat += "\\ "
    elif r < 0.2:
        pat += "\\  "
    elif r < 0.23:
        pat += "\t"
    return pat


def rand_file_text(rng, names_pool):
    lines = []
    for _ in range(rng.randint(1, 7)):
        r = rng.random()
        if r < 0.1:
            lines.append("")
        elif r < 0.17:
            lines.append("# comment " + rng.choice(names_pool))
        elif r < 0.45:
            name = rng.choice(names_pool)
            lines.append(rng.choice(["", "!", "/", "**/"]) + name + rng.choice(["", "", "/"]))
        else:
            lines.append(rand_pattern(rng))
    eol = "\r\n" if rng.random() < 0.15 else "\n"
    text = eol.join(lines)
    if rng.random() < 0.8:
        text += eol
    if rng.random() < 0.1:
        text = "\ufeff" + text
    return text


def build_case(rng):
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(REPO)
    os.makedirs(HOME)
    subprocess.run(["git", "init", "-q", REPO], check=True, env=git_env(False))
    dirs = [""]
    for _ in range(rng.randint(1, 7)):
        parent = rng.choice(dirs)
        if parent.count("/") >= 2:
            continue
        d = (parent + "/" if parent else "") + rng.choice(DIRNAMES)
        if d not in dirs:
            dirs.append(d)
    files = []
    for d in dirs:
        os.makedirs(os.path.join(REPO, d), exist_ok=True)
    for d in dirs:
        for _ in range(rng.randint(0, 5)):
            name = rng.choice(NAMES)
            path = (d + "/" if d else "") + name
            full = os.path.join(REPO, path)
            if os.path.isdir(full):
                continue
            with open(full, "w") as f:
                f.write("x")
            files.append(path)
    pool = NAMES + DIRNAMES
    for d in dirs:
        if rng.random() < 0.55:
            with open(os.path.join(REPO, d, ".gitignore"), "w", newline="") as f:
                f.write(rand_file_text(rng, pool))
    if rng.random() < 0.5:
        with open(os.path.join(REPO, ".git/info/exclude"), "w", newline="") as f:
            f.write(rand_file_text(rng, pool))
    use_xdg = rng.random() < 0.3
    r = rng.random()
    if r < 0.35:
        key = rng.choice(["excludesFile", "excludesfile", "EXCLUDESFILE", "ExcludesFile"])
        where = rng.choice(["~/globalignore", HOME + "/globalignore", "globalignore.txt", "\"~/globalignore\""])
        with open(os.path.join(REPO, ".git/config"), "a") as f:
            f.write(f"[core]\n\t{key} = {where}\n")
        target = where.strip('"')
        target = HOME + target[1:] if target.startswith("~/") else target
        target = target if target.startswith("/") else os.path.join(REPO, target)
        with open(target, "w", newline="") as f:
            f.write(rand_file_text(rng, pool))
    else:
        for p in ([XDG + "/git/ignore"] if use_xdg else []) + [HOME + "/.config/git/ignore"]:
            if rng.random() < 0.6:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", newline="") as f:
                    f.write(rand_file_text(rng, pool))
    return dirs, files, use_xdg


def git_env(use_xdg):
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": HOME, "GIT_CONFIG_NOSYSTEM": "1",
           "LC_ALL": "C"}
    if use_xdg:
        env["XDG_CONFIG_HOME"] = XDG
    return env


def run(cmd, env):
    p = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True)
    return p.returncode, p.stdout.decode("utf-8", "surrogateescape"), p.stderr.decode("utf-8", "surrogateescape")


def main():
    rng = random.Random(SEED)
    bad = 0
    for i in range(N):
        dirs, files, use_xdg = build_case(rng)
        env = git_env(use_xdg)
        g_rc, g_list, g_err = run(["git", "ls-files", "--others", "--exclude-standard"], env)
        m_rc, m_list, m_err = run([GLEANER, "list"], env)
        paths = [p for p in dirs if p] + files
        rng.shuffle(paths)
        gc_rc, g_chk, gc_err = run(["git", "check-ignore", "-v", "-n", "--"] + paths, env) if paths else (0, "", "")
        mc_rc, m_chk, mc_err = run([GLEANER, "check", "--"] + paths, env) if paths else (0, "", "")
        if g_list != m_list or g_chk != m_chk or m_rc != 0:
            bad += 1
            if bad <= 3:
                print(f"=== case {i} seed {SEED} xdg={use_xdg}")
                subprocess.run(["bash", "-c", f"cd {REPO} && find . -path ./.git/hooks -prune -o -type f -print | sort; for f in $(find . -name .gitignore) .git/info/exclude; do echo \"--- $f\"; cat -A \"$f\"; done; tail -3 .git/config; ls -la {HOME} {HOME}/.config/git {XDG}/git 2>/dev/null; for f in {HOME}/globalignore {REPO}/globalignore.txt {HOME}/.config/git/ignore {XDG}/git/ignore; do [ -f $f ] && echo \"--- $f\" && cat -A $f; done"])
                if g_list != m_list:
                    print("LIST git:\n" + g_list + "LIST gleaner:\n" + m_list + m_err)
                if g_chk != m_chk:
                    gl, ml = g_chk.splitlines(), m_chk.splitlines()
                    for a, b in zip(gl, ml):
                        if a != b:
                            print(f"  git:     {a!r}\n  gleaner: {b!r}")
                    if len(gl) != len(ml):
                        print("check len differ", len(gl), len(ml), mc_err, gc_err)
    print(f"seed {SEED}: {N} cases, {bad} mismatching")


main()
