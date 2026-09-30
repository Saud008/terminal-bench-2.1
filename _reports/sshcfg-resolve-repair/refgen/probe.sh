#!/bin/bash
mkdir -p /root/.ssh/conf.d
g() { ssh -G "$@" 2>&1 | grep -E '^(host|user|hostname|port|identityfile|sendenv|setenv|proxycommand|proxyjump|connecttimeout|controlpath|userknownhostsfile|localforward|dynamicforward|remoteforward|stricthostkeychecking|controlmaster|controlpersist|forwardagent|loglevel|hostkeyalias|remotecommand|serveraliveinterval|certificatefile|identitiesonly) ' ; echo "rc=${PIPESTATUS[0]}"; }

echo "== 1 host case"
cat > /tmp/c1 <<'EOF'
Host web1
  User alice
Match final
  Port 2200
Host web1
  User bob
  SendEnv FOO
Host *
  SendEnv BAR
EOF
g -F /tmp/c1 WEB1

echo "== 2 sendenv dup final pass"
cat > /tmp/c2 <<'EOF'
Host *
  SendEnv LANG LC_*
  IdentityFile ~/.ssh/a
Match final
  User z
EOF
g -F /tmp/c2 x

echo "== 3 proxycommand comment & proxyjump"
cat > /tmp/c3 <<'EOF'
Host a
  ProxyCommand nc %h %p # comment here
Host b
  ProxyJump u1@j1:2222,u2@j2:23
  ProxyCommand foo
Host c
  ProxyJump none
Host c
  ProxyCommand bar %h
Host d
  ProxyJump 10.0.0.1:2022
EOF
g -F /tmp/c3 a; g -F /tmp/c3 b; g -F /tmp/c3 c; g -F /tmp/c3 d

echo "== 4 connecttimeout none"
cat > /tmp/c4 <<'EOF'
Host *
  ConnectTimeout none
  ConnectTimeout 1m30s
  ServerAliveInterval 2m
  ControlPersist 10m
  ControlMaster yes
  StrictHostKeyChecking no
  LogLevel debug
  HostKeyAlias WebAlias
  ControlPath ~/.ssh/cm-%r@%h:%p-%n
  UserKnownHostsFile ~/.ssh/kh-%h /etc/x
  RemoteCommand echo %h %r %%
  ForwardAgent ~/agent.sock
  HostName %h.Corp.Example
  LocalForward 8080 localhost:80
  LocalForward [::1]:9090 db:5432
  DynamicForward 1080
  RemoteForward 2222 /tmp/sock
  LocalForward 8080 localhost:80
  SetEnv A=1 B=2 A=3
  SetEnv C=4
  CertificateFile ~/.ssh/c.pub
EOF
g -F /tmp/c4 -l bob Host5

echo "== 5 include relative + inactive"
cat > /root/.ssh/conf.d/10-a.conf <<'EOF'
User fromA
Host inc
  Port 1111
EOF
cat > /root/.ssh/conf.d/02-b.conf <<'EOF'
IdentityFile ~/.ssh/fromB
Host *
  SetEnv FROMB=1
EOF
cat > /tmp/c5 <<'EOF'
Host nomatch
  Include conf.d/*.conf
Host inc
  Include conf.d/*.conf
  ServerAliveInterval 7
Port 5555
EOF
g -F /tmp/c5 inc; g -F /tmp/c5 other

echo "== 6 negation"
cat > /tmp/c6 <<'EOF'
Host *.corp !bastion.corp
  User corpuser
Host !bastion.corp
  Port 23
Host web,db
  Port 24
Match host "*.corp,!db.corp" user root
  IdentityFile ~/.ssh/m
EOF
g -F /tmp/c6 bastion.corp; g -F /tmp/c6 app.corp; g -F /tmp/c6 db.corp; g -F /tmp/c6 web,db

echo "== 7 match host uses hostname"
cat > /tmp/c7 <<'EOF'
Host short
  HostName long.example.net
Match host long.example.net
  User viahost
Match originalhost short
  Port 2022
Host long.example.net
  IdentityFile ~/.ssh/pass1
Match final host long.example.net
  IdentityFile ~/.ssh/final
EOF
g -F /tmp/c7 short

echo "== 8 -o first wins"
cat > /tmp/c8 <<'EOF'
Host *
  User cfg
  Port 99
EOF
g -F /tmp/c8 -o User=opt -o "Port 77" h; g -F /tmp/c8 ssh://uri@h2:2020

echo "== 9 sendenv removal"
cat > /tmp/c9 <<'EOF'
Host *
  SendEnv LANG LC_ALL LC_CTYPE XMODIFIERS
Host x
  SendEnv -LC_* TERM
  SendEnv -LAN
EOF
g -F /tmp/c9 x

echo "== 10 errors"
printf 'Host a\n  Bogus 1\n' > /tmp/c10; g -F /tmp/c10 a
printf 'IgnoreUnknown Bog*\nBogus 1\nUser u\n' > /tmp/c11; g -F /tmp/c11 a
printf 'Match all host a\n' > /tmp/c12; g -F /tmp/c12 a
printf 'Port=2022\nUser = eq\nIdentityFile "~/.ssh/my key"\n' > /tmp/c13; g -F /tmp/c13 a
