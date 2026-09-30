"""Shared fixture runner: materialise a case's config tree and run a resolver."""
import os
import shutil
import subprocess

SSH_DIR = "/root/.ssh"
KEYWORDS = [
    "host", "user", "hostname", "port", "batchmode", "controlmaster",
    "identitiesonly", "stricthostkeychecking", "serveralivecountmax",
    "serveraliveinterval", "controlpath", "hostkeyalias", "remotecommand",
    "loglevel", "dynamicforward", "localforward", "remoteforward",
    "identityfile", "certificatefile", "userknownhostsfile", "sendenv",
    "setenv", "forwardagent", "connecttimeout", "controlpersist",
    "proxycommand", "proxyjump",
]
KWSET = set(KEYWORDS)
EXTRA_ROOTS = ["/srv/hopcfg-fixture"]


def materialise(files):
    for d in [SSH_DIR] + EXTRA_ROOTS:
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(SSH_DIR, mode=0o700)
    for rel, content in files.items():
        path = rel if rel.startswith("/") else os.path.join(SSH_DIR, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        os.chmod(path, 0o644)


def run(cmd_prefix, case):
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/root",
           "USER": "root", "LOGNAME": "root", "LC_ALL": "C"}
    env.update(case.get("env", {}))
    materialise(case["files"])
    p = subprocess.run(cmd_prefix + case["args"], capture_output=True,
                       text=True, env=env, stdin=subprocess.DEVNULL,
                       cwd="/tmp", timeout=30)
    return p.returncode, p.stdout


def filter_ssh(stdout):
    out = []
    for line in stdout.splitlines():
        kw = line.split(" ", 1)[0]
        if kw in KWSET:
            out.append(line)
    return "".join(l + "\n" for l in out)
