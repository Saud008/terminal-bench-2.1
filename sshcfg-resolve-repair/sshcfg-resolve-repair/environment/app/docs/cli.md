# hopcfg command line and output

    hopcfg [-F configfile] [-l login_name] [-o option] [-p port] destination

`destination` is `[user@]host` or `ssh://[user@]host[:port]`. The options have
the same meaning as for `ssh`:

| Option | Meaning |
|---|---|
| `-F file` | read `file` as the user configuration instead of `~/.ssh/config`; `-F none` reads nothing |
| `-l user` | login name |
| `-o 'Keyword value'` | a configuration line; may be repeated |
| `-p port` | port |

The system-wide `/etc/ssh/ssh_config` is never read.

## Output

On success `hopcfg` exits 0 and writes one `keyword value` line per setting to
standard output, in this order (lines whose value is unset are omitted, list
keywords print one line per entry):

    host
    user
    hostname
    port
    batchmode
    controlmaster
    identitiesonly
    stricthostkeychecking
    serveralivecountmax
    serveraliveinterval
    controlpath
    hostkeyalias
    remotecommand
    loglevel
    dynamicforward
    localforward
    remoteforward
    identityfile
    certificatefile
    userknownhostsfile
    sendenv
    setenv
    forwardagent
    connecttimeout
    controlpersist
    proxycommand  (or proxyjump)

For these keywords the output must be byte-identical to the corresponding
lines of `ssh -G` from Debian bookworm `openssh-client 1:9.2p1-2+deb12u10`,
run with the same arguments by the same user; every other line `ssh -G`
prints is out of scope.

On any error (bad configuration line, bad destination, jump host loop, ...)
`hopcfg` writes a diagnostic to standard error, nothing to standard output,
and exits 255.

## Known differences from ssh

- `CanonicalizeHostname` values other than `no` and `Match exec` are rejected.
- The `%C`, `%l` and `%L` tokens are rejected.
- Keywords outside the list above are syntax-checked by keyword name only;
  their values are not validated.
- Configuration file ownership and permissions are not checked.
