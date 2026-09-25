# backup_label contract

Required lines in archive_root/backup_label:

| Line prefix | Meaning |
|-------------|---------|
| START TIME: | UTC timestamp YYYY-MM-DD HH:MM:SS UTC |
| START TIMELINE: | Decimal timeline id at backup start |
| START WAL LOCATION: | Contains file TTTTTTTTSSSSSSSSSSSSSSSS token |

Whitespace around START TIME value is ignored after trim.

START TIME must parse as UTC, not local timezone.
