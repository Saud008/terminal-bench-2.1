# Console dump format

Rspamdctl fuzzy dump lines (one per indexed hash):

    hash=<16 hex chars> epoch=<int> algo=<int>

Hex digits may appear in either case in the fixture file. The parser must normalize hash to lowercase before comparing to sqlite hash values.

console_lines_matched in the rotation summary is the count of dump lines that matched an index row on hash, epoch, and algo after normalization.

Verification fails if any line fails to match or if matched count differs from distinct hashes in the index for the active epoch.

Negative-path verification may supply an alternate dump file such as bad-console.dump under /app/output to force console_mismatch rollback handling.
