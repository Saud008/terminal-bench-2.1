# Apt sources contract

Append one suite line to {tree}/etc/apt/sources.list.d/debian-stage2.list:

deb http://deb.debian.org/debian {codename} main

where codename comes from meta.json.

When meta.json suite_retry is greater than zero, the sources stage runs twice in one audit invocation. The file must contain exactly one suite line after both passes (idempotent append).

sources_digest in the export manifest is sha256 of the final file contents.
