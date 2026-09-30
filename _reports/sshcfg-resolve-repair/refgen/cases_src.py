"""Hidden verifier fixtures.  Expected output is recorded from real ssh -G."""

GROUPS = {}


def group(name):
    GROUPS.setdefault(name, [])
    return GROUPS[name]


def add(name, config, hosts, extra=(), files=None, env=None, cfg="config"):
    tree = {cfg: config}
    if files:
        tree.update(files)
    for h in hosts:
        case = {"files": tree, "args": ["-F", "/root/.ssh/" + cfg, *extra, h]}
        if env:
            case["env"] = env
        group(name).append(case)


# ---------------------------------------------------------------- host lines
add("host_patterns", """\
Host *.prod.example.net !jump.prod.example.net
    User deploy
    IdentityFile ~/.ssh/prod_ed25519
Host !legacy-* !*.lab
    ServerAliveInterval 45
Host legacy-* web? db[12]
    Port 2222
Host *
    User fallback
    Port 22
""", ["api.prod.example.net", "jump.prod.example.net", "legacy-mail",
      "web1", "web12", "db[12]", "ci.lab"])

add("host_patterns", """\
Host Build-Farm
    User farmer
Host build-farm
    Port 2200
Host *-farm !*-FARM
    IdentitiesOnly yes
Host a,b
    Port 2300
""", ["Build-Farm", "build-farm", "BUILD-FARM", "a", "a,b"])

add("host_patterns", """\
Host !*.internal
Host bastion !bastion
    User nobody
Host "gw 1" gw2
    Port 2400
Host gw?
    User gwuser
""", ["bastion", "gw2", "gw1", "x.internal"])

add("host_patterns", """\
Host !staging-* app-* *-db
    User app
    Port 2500
Host !*-canary *-canary-? edge-*
    IdentitiesOnly yes
Host staging-* !staging-db
    User stage
""", ["app-1", "staging-db", "staging-web", "edge-canary-1", "edge-2"])

# ---------------------------------------------------------------- Match
add("match_criteria", """\
Host db
    HostName db01.dc2.example.org
Host cache
    HostName %h.dc2.example.org
Match host *.dc2.example.org
    User dc2ops
Match originalhost db
    Port 2201
Match host db !originalhost cache
    IdentityFile ~/.ssh/by-alias
Match host "*.dc2.example.org,!cache.*"
    IdentityFile ~/.ssh/dc2-not-cache
Match user dc2ops
    ServerAliveCountMax 9
Match !user root localuser root
    ConnectTimeout 7
""", ["db", "cache", "db01.dc2.example.org", "other"])

add("match_criteria", """\
Match user admin*,!admin-ro
    IdentitiesOnly yes
    Port 2022
Match localuser root !host *.corp
    LogLevel VERBOSE
Match all
    User fallback
""", ["srv.corp", "srv.home"], extra=["-l", "admin-ops"])

add("match_criteria", """\
Match user admin*,!admin-ro
    IdentitiesOnly yes
    Port 2022
Match localuser root !host *.corp
    LogLevel VERBOSE
Match all
    User fallback
""", ["srv.corp"], extra=["-l", "admin-ro"])

add("match_criteria", """\
Host short
    HostName Long.Example.NET
Match host long.example.net
    User viahost
Match host short
    Port 1111
Match canonical
    Port 3333
Match !canonical host long.*
    IdentityFile ~/.ssh/pass-one
""", ["short", "long.example.net"])

# ---------------------------------------------------------------- final pass
add("final_pass", """\
Host web1
    User alice
Match final
    Port 2200
Host web1
    User bob
    SendEnv FOO_*
Host *
    SendEnv LANG
    IdentityFile ~/.ssh/common
""", ["WEB1", "web1"])

add("final_pass", """\
Host app
    HostName app-01.int.example.com
Host app-01.int.example.com
    User from-resolved
    IdentityFile ~/.ssh/resolved
Match final host app-01.*
    Port 2202
    IdentityFile ~/.ssh/final
Match originalhost app final
    ServerAliveInterval 30
Host app
    LocalForward 5432 db.int:5432
""", ["app", "app-01.int.example.com"])

add("final_pass", """\
Host edge
    HostName 10.20.30.40
Host 10.20.30.40
    User by-address
Match host nothing final
    User never
Host edge
    SetEnv STAGE=one
""", ["edge", "EDGE"])

add("final_pass", """\
Host *
    SendEnv LC_*
Match final
    SendEnv -LC_ALL
Host srv
    SendEnv LC_ALL TZ
""", ["srv"])

# ---------------------------------------------------------------- Include
INC_MAIN = """\
Include conf.d/*.conf
Host jump
    Include hosts/jump.conf
    ServerAliveInterval 11
Host nomatch-*
    Include hosts/*.conf
Port 2600
"""
INC_FILES = {
    "conf.d/20-team.conf": "User team\nHost team-*\n    Port 2020\n",
    "conf.d/05-base.conf": "IdentityFile ~/.ssh/base\nHost *\n    SendEnv BASE_*\n",
    "conf.d/README": "this is not a config file\n",
    "hosts/jump.conf": "HostName jump.edge.example.com\nHost jump\n    User jumper\nHost other\n    Port 9\n",
    "hosts/zz.conf": "Host *\n    Compression yes\n    SetEnv FROM_ZZ=1\n",
}
add("include_scoping", INC_MAIN, ["jump", "team-a", "nomatch-1", "elsewhere"],
    files=INC_FILES)

add("include_scoping", """\
Host alpha
    Include parts/alpha.conf
    User alpha-after
Host beta
    Include parts/missing-*.conf
    User beta-after
Match host gamma
    Include parts/gamma.conf
IdentityFile ~/.ssh/tail
""", ["alpha", "beta", "gamma"], files={
    "parts/alpha.conf": "Port 2001\nHost *\n    SetEnv SEEN=alpha\nHost zzz\n",
    "parts/gamma.conf": "Match all\n    Port 2003\nHost nope\n",
})

add("include_scoping", """\
Host outer
    Include level1.conf
Host *
    IdentityFile ~/.ssh/after
""", ["outer", "inner", "unrelated"], files={
    "level1.conf": "Include level2.conf\nHost inner\n    Port 2102\n",
    "level2.conf": "User l2\nHost *\n    ServerAliveCountMax 5\n",
})

add("include_scoping", """\
Include stack.d/*.conf
Host solo
    Include stack.d/*.conf
""", ["solo", "pair-b", "x"], files={
    "stack.d/a.conf": "Host pair-*\n    Port 2701\nHost unused-host\n",
    "stack.d/b.conf": "User stack-b\nHost pair-b\n    IdentitiesOnly yes\n",
    "stack.d/c.conf": "Host solo\n    SendEnv STACK_C\nHost other\n",
    "stack.d/d.conf": "ServerAliveCountMax 8\n",
})

add("include_paths", """\
Include fleet.d/*.conf
Include /srv/hopcfg-fixture/shared.conf
Include ~/.ssh/personal.conf
""", ["db-main", "cache-01", "laptop"], files={
    "fleet.d/10-db.conf": "Host db-*\n    User dba\n",
    "fleet.d/02-cache.conf": "Host cache-*\n    User cacheops\n    Port 6380\n",
    "/srv/hopcfg-fixture/shared.conf": "Host *\n    ServerAliveInterval 20\n",
    "/srv/hopcfg-fixture/fleet.d/10-db.conf": "Host db-*\n    User wrong-dir\n    Port 1\n",
    "personal.conf": "Host laptop\n    User me\n",
}, cfg="config")

add("include_paths", """\
Include sub/*.conf
""", ["x1", "y2"], files={
    "sub/b.conf": "Host *\n    User from-b\n",
    "sub/a.conf": "Host x*\n    User from-a\n",
    "/srv/hopcfg-fixture/sub/a.conf": "Host *\n    User wrong\n",
}, cfg="nested/main.conf")

add("include_paths", """\
Host bastion
    Include ../outside.conf
    Include bastion.d/*
""", ["bastion"], files={
    "outside.conf": "User relative-to-dot-ssh\n",
    "../outside.conf": "User parent-of-dot-ssh\n",
    "bastion.d/2": "Port 2402\n",
    "bastion.d/10": "Port 2410\n",
    "bastion.d/1": "IdentityFile ~/.ssh/one\n",
})

# ---------------------------------------------------------------- precedence
add("first_value_wins", """\
Host *.example.com
    User cfg-user
    Port 2100
    StrictHostKeyChecking accept-new
    IdentityFile ~/.ssh/cfg
Host *
    User default-user
    Port 22
    StrictHostKeyChecking yes
""", ["a.example.com"], extra=["-o", "User=opt-user", "-p", "2999",
                               "-o", "IdentityFile ~/.ssh/cli"])

add("first_value_wins", """\
Host *
    User cfg
    Port 99
""", ["ops@box", "ssh://uri-user@box:2022", "ssh://box"],
    extra=["-o", "Port=77"])

add("first_value_wins", """\
Host box
    User cfg
""", ["other@box"], extra=["-l", "cli-user"])

add("first_value_wins", """\
Host box
    HostName box.a.example
    HostName box.b.example
    ControlMaster auto
    ControlMaster no
    LogLevel ERROR
Host *
    LogLevel DEBUG3
""", ["box"], extra=["-o", "LogLevel=QUIET"])

# ---------------------------------------------------------------- lists
add("sendenv_setenv", """\
Host *
    SendEnv LANG LC_ALL LC_CTYPE LC_MESSAGES XMODIFIERS
Host dev*
    SendEnv -LC_* TERM
    SendEnv -LAN
    SendEnv -XMODIFIERS EDITOR
Host dev-noisy
    SendEnv LC_TIME
""", ["dev1", "dev-noisy", "prod"])

add("sendenv_setenv", """\
Host api
    SetEnv APP_ENV=staging TRACE=0 APP_ENV=prod
Host *
    SetEnv TRACE=1 REGION=eu
    SetEnv LATE=1
""", ["api", "other"])

add("sendenv_setenv", """\
Host one
    SendEnv A_*
Host *
    SendEnv -A_? B
    SetEnv "MSG=hello world" X=1
""", ["one", "two"])

add("list_keywords", """\
Host multi
    IdentityFile ~/.ssh/k1
    IdentityFile ~/.ssh/k2
    CertificateFile ~/.ssh/k1-cert.pub
Host *
    IdentityFile ~/.ssh/k1
    IdentityFile "~/.ssh/key with space"
    CertificateFile ~/.ssh/k1-cert.pub
    CertificateFile ~/.ssh/other-cert.pub
    UserKnownHostsFile ~/.ssh/kh_%h /etc/ssh/extra_known
    UserKnownHostsFile /ignored
""", ["multi", "single"])

add("list_keywords", """\
Host tun
    LocalForward 8080 localhost:80
    LocalForward [::1]:9090 db.internal:5432
    LocalForward 127.0.0.1:3306 /var/run/mysqld.sock
    LocalForward 8080 localhost:80
    DynamicForward 1080
    DynamicForward localhost:1081
    RemoteForward 2222 localhost:22
    RemoteForward 10022
    RemoteForward /tmp/remote.sock /tmp/local-%r.sock
Host clear
    LocalForward 7000 a:7000
    ClearAllForwardings yes
    RemoteForward 7001 b:7001
Host *
    UserKnownHostsFile none
""", ["tun", "clear"])

# ---------------------------------------------------------------- times
add("time_values", """\
Host slow
    ConnectTimeout 1m30s
    ServerAliveInterval 2m
    ControlPersist 1h5m
Host flaky
    ConnectTimeout none
    ConnectTimeout 45s
    ServerAliveInterval 1w
    ControlPersist yes
Host short
    ConnectTimeout 90
    ControlPersist 0
    ServerAliveInterval 1H1M1S
Host *
    ConnectTimeout 5
    ControlPersist 10m
    ServerAliveCountMax 4
""", ["slow", "flaky", "short", "any"])

add("time_values", """\
Host batch-*
    BatchMode yes
Host batch-keep
    ServerAliveInterval 0
Host interactive
    BatchMode no
    ProtocolKeepAlives 25
Host legacy
    SetupTimeOut 3m
""", ["batch-job", "batch-keep", "interactive", "legacy"])

add("time_values", """\
Host *
    BatchMode yes
    ServerAliveInterval none
""", ["b"], extra=["-o", "ServerAliveInterval=2d"])

# ---------------------------------------------------------------- proxy
add("proxy_settings", """\
Host inner-*
    ProxyJump ops@jump1.example.com:2222,jump2.example.com
Host inner-direct
    ProxyCommand none
Host legacy
    ProxyCommand /usr/bin/nc -X connect -x proxy:3128 %h %p # corp proxy
    ProxyJump jump9
Host v6
    ProxyJump [2001:db8::7]:2022
Host v4
    ProxyJump admin@192.0.2.10
Host nojump
    ProxyJump none
    ProxyCommand ssh -W %h:%p fallback
Host *
    ProxyJump default-jump
""", ["inner-a", "inner-direct", "legacy", "v6", "v4", "nojump", "plain"])

add("proxy_settings", """\
Host first-cmd
    ProxyCommand nc %h 22
Host *
    ProxyJump later
""", ["first-cmd", "other"])

add("proxy_settings", """\
Host loop
    HostName jump.example.com
    ProxyJump jump.example.com
""", ["loop"])

# ---------------------------------------------------------------- expansion
add("token_expansion", """\
Host ci-*
    HostName %h.Build.Example.COM
    User builder
    ControlPath ~/.ssh/cm/%r@%h:%p
    RemoteCommand cd /srv/%n && exec $SHELL -l # %% literal
    HostKeyAlias CI-Pool
Host upper
    HostName DB.Example.COM
Host v6lit
    HostName FE80:0:0:0::1
Host shortip
    HostName 10.1
Host *
    UserKnownHostsFile ~/.ssh/known_hosts.d/%k ${HOPCFG_KH}
    ControlPath /run/cm-%u-%i-%d-%p
""", ["ci-Runner7", "upper", "v6lit", "shortip"],
    env={"HOPCFG_KH": "/etc/ssh/fleet_known_hosts"})

add("token_expansion", """\
Host agent
    ForwardAgent ~/.agent/%h.sock
Host agentenv
    ForwardAgent ${HOPCFG_AGENT}
Host agentno
    ForwardAgent no
    ForwardAgent /tmp/agent-%r
Host *
    ControlPath ~/.ssh/%n-%p-%r
    RemoteCommand echo %h %p %r %u %d %i %%h
""", ["agent", "agentenv", "agentno"], extra=["-l", "tok"],
    env={"HOPCFG_AGENT": "/run/agent.sock"})

# ---------------------------------------------------------------- errors
REJECT = {
    "unknown": "Host a\n    Frobnicate yes\n",
    "missing_arg": "Host a\n    User\n",
    "extra_args": "Host a\n    Port 22 23\n",
    "bad_match": "Match host a all\n",
    "bad_match_attr": "Match hostname a\n    User x\n",
    "bad_quotes": "Host a\n    IdentityFile \"~/.ssh/k\n",
    "bad_port": "Host a\n    Port 70000\n",
    "bad_time": "Host a\n    ConnectTimeout 5x\n",
    "bad_sendenv": "Host a\n    SendEnv FOO=bar\n",
    "bad_setenv": "Host a\n    SetEnv FOO\n",
    "bad_fwd": "Host a\n    LocalForward 8080\n",
    "bad_jump": "Host zzz\n    ProxyJump user@:22\n",
    "inactive_bad": "Host never-matches\n    Bogus value\n",
    "include_bad": "Include bad.conf\n",
    "bad_token": "Host a\n    HostName %h.%q\n",
    "bad_ukh": "Host a\n    UserKnownHostsFile none /x\n",
}
for key, conf in REJECT.items():
    add("rejected_configs", conf, ["a"],
        files={"bad.conf": "Host *\n    Bogus 1\n"} if key == "include_bad" else None)
add("rejected_configs", "IgnoreUnknown Frob*,UseKeychain\nFrobnicate 1\nUseKeychain yes\nUser ok\n", ["a"])
add("rejected_configs", "Host *\n    User ok\n", ["bad,host", "-lead"], extra=[])
add("rejected_configs", "Host *\n    User ok\n", ["a"], extra=["-o", "Host=b"])
add("rejected_configs", "Host *\n    User ok\n", ["a"], extra=["-o", "Include=x"])

# ---------------------------------------------------------------- formats
add("value_formats", """\
HOST=fmt1
  stricthostkeychecking=NO
  CONTROLMASTER Yes
  loglevel debug1
  identitiesonly=true
  batchmode False
Host = fmt2
    StrictHostKeyChecking off
    ControlMaster autoask
    LogLevel verbose
Host fmt3
    StrictHostKeyChecking accept-new
    ControlMaster ask
    LogLevel DEBUG2
	Port	=	2345
Host fmt4
    StrictHostKeyChecking true
    ControlMaster auto
    User "quoted user"
    LogLevel quiet
Host fmt5
    LogLevel Silent
    StrictHostKeyChecking ask
""", ["fmt1", "fmt2", "fmt3", "fmt4", "fmt5"])
