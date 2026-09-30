"""Random differential fuzzing of hopcfg against ssh -G."""
import random
import sys

sys.path.insert(0, "/w")
import harness  # noqa: E402

HOSTS = ["web1", "WEB1", "db.corp", "app.prod.example.net", "jump", "10.0.0.5",
         "x", "cache-01", "Mixed.Case"]
PATTERNS = ["*", "web?", "*.corp", "!db.corp", "!*.corp", "WEB1", "jump",
            "*.example.net", "!x", "cache-*", "10.0.0.*", "mixed.case", "Mixed.*"]
MATCH_CRIT = ["host *.corp", "host web1,!db.*", "originalhost WEB1", "!host jump",
              "user root", "user deploy*", "localuser root", "final", "!final",
              "canonical", "host 10.0.0.5", "originalhost x final", "all"]
OPTS = [
    "User deploy", "User %h", "User admin", "Port 2200", "Port 23",
    "HostName %h.example.org", "HostName Real.Example.ORG", "HostName 10.0.0.9",
    "IdentityFile ~/.ssh/a", "IdentityFile ~/.ssh/b", "IdentityFile ~/.ssh/%h",
    "CertificateFile ~/.ssh/c.pub", "SendEnv LANG LC_*", "SendEnv -LC_*",
    "SendEnv -L*", "SendEnv TZ", "SetEnv A=1 B=2", "SetEnv A=3",
    "ProxyJump j1", "ProxyJump u@j2:2022,j3", "ProxyJump none",
    "ProxyCommand nc %h %p", "ProxyCommand none",
    "ConnectTimeout 1m", "ConnectTimeout none", "ConnectTimeout 2h3s",
    "ServerAliveInterval 30", "ServerAliveInterval 1m30s", "BatchMode yes",
    "BatchMode no", "ControlPersist 5m", "ControlPersist yes", "ControlPersist no",
    "ControlMaster auto", "ControlPath ~/.ssh/cm-%r@%h:%p",
    "StrictHostKeyChecking accept-new", "StrictHostKeyChecking no",
    "LogLevel DEBUG1", "LogLevel quiet", "HostKeyAlias Alias-%h",
    "LocalForward 8000 localhost:80", "DynamicForward 1080",
    "RemoteForward 9000 localhost:9000", "ForwardAgent yes",
    "ForwardAgent ~/agent.sock", "IdentitiesOnly yes",
    "UserKnownHostsFile ~/.ssh/kh1 ~/.ssh/kh2", "ClearAllForwardings yes",
    "RemoteCommand echo %n %h", "ServerAliveCountMax 7", "Compression yes",
]


def rand_block(rng, depth, files, prefix):
    lines = []
    for _ in range(rng.randint(1, 7)):
        r = rng.random()
        if r < 0.2:
            pats = " ".join(rng.sample(PATTERNS, rng.randint(1, 3)))
            lines.append(f"Host {pats}")
        elif r < 0.33:
            crit = rng.sample(MATCH_CRIT, rng.randint(1, 2))
            if "all" in crit and len(crit) > 1:
                crit.remove("all")
            lines.append("Match " + " ".join(crit))
        elif r < 0.43 and depth < 2:
            name = f"{prefix}{len(files)}.conf"
            files[f"inc/{name}"] = rand_block(rng, depth + 1, files, prefix + "i")
            lines.append(rng.choice([f"Include inc/{name}", "Include inc/*.conf"]))
        for _ in range(rng.randint(1, 4)):
            lines.append("    " + rng.choice(OPTS))
    return "\n".join(lines) + "\n"


def main():
    binary = sys.argv[1]
    n = int(sys.argv[2])
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    rng = random.Random(seed)
    bad = 0
    ok_rc = 0
    outs = set()
    for i in range(n):
        files = {}
        files["config"] = rand_block(rng, 0, files, "f")
        host = rng.choice(HOSTS)
        extra = []
        if rng.random() < 0.2:
            extra = ["-l", rng.choice(["deploy", "root", "zed"])]
        case = {"files": files, "args": ["-F", "/root/.ssh/config", *extra, host]}
        src, sout = harness.run(["ssh", "-G"], case)
        exp = harness.filter_ssh(sout) if src == 0 else ""
        ok_rc += src == 0
        outs.add(exp)
        hrc, hout = harness.run([binary], case)
        if (src, exp) != (hrc, hout):
            bad += 1
            if bad <= 5:
                print(f"### case {i} args={case['args']}")
                for k, v in files.items():
                    print(f"--- {k}\n{v}")
                print(f"ssh rc={src}\n{exp}hopcfg rc={hrc}\n{hout}")
    print(f"fuzz: {n - bad}/{n} match (ssh rc0={ok_rc}, distinct outputs={len(outs)})")


if __name__ == "__main__":
    main()
