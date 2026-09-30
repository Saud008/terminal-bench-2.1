# hopcfg

`hopcfg` resolves an OpenSSH client configuration for one destination and
prints the effective settings, the same way `ssh -G` does, without needing an
ssh binary on the machine. Fleet tooling uses it to pre-compute jump chains,
control sockets and forwards from the `ssh_config` files it ships to hosts.

The compatibility target is the `ssh -G` output of Debian bookworm's
`openssh-client` package, version `1:9.2p1-2+deb12u10`, restricted to the
keywords listed in [docs/cli.md](docs/cli.md).

## Building

    make            # builds ./hopcfg (C11, libc only)
    make check      # smoke tests in smoke/
    make install    # PREFIX=/usr/local

## Layout

    src/main.c        command line, destination parsing, the two resolution passes
    src/readconf.c    per-line keyword handling, Host and Include
    src/matchcfg.c    Match criteria
    src/keywords.c    keyword table
    src/options.c     option defaults
    src/dump.c        output
    src/jump.c        ProxyJump parsing
    src/forward.c     Local/Remote/DynamicForward parsing
    src/expand.c      %-token, ${ENV} and ~ expansion
    src/hostspec.c    host/user/port and ssh:// parsing, address checks
    src/match.c       wildcard pattern matching
    src/convtime.c    time values and port numbers
    src/tokens.c      line tokenizer
    src/strlist.c     string lists
    src/log.c         diagnostics
    src/xmalloc.c     allocation helpers
    examples/         sample configurations (fleet.conf, workstation.conf,
                      ci-runner.conf)
    smoke/            smoke tests: cases/<name>/{config,args,expected}
