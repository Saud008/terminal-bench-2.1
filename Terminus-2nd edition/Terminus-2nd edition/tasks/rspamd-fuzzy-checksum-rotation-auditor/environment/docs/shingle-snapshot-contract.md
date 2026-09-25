# Shingle snapshot contract

Path: /app/state/shingle-snapshot.json

Written before sqlite mutation on every rotate (including dry-run).

Fields:

- schema: 1
- mails: array of mail_id strings from mails.tsv in file sequence
- mail_digest: sha256 hex of JSON array of mail_id strings using compact separators
- epoch_salt: manifest epoch_salt plus RF_EPOCH_SALT_SUFFIX when set

Only mail_id values listed in mails.tsv are included; ignore other .eml files present in the corpus directory (including decoy.eml scratch files created during verification).
