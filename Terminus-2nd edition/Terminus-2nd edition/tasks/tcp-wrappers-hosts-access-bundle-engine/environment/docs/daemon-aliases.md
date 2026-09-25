# Daemon aliases

A bundle may ship alias data beside its manifest, either as `daemon-aliases.json` or via a path in `manifest.json` (`daemon_aliases`).

Example:

```json
{
  "sshd": ["SSHD", "secure-shell"],
  "ftp": ["ftpd", "FTP"]
}
```

Keys are canonical daemon names. Values list alternate spellings that must be treated as the same service for rule matching and decide exports.

If a bundle omits alias data, only literal daemon names from the fragments apply.
