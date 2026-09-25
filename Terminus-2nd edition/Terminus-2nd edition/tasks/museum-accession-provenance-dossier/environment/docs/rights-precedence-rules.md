# Rights restriction precedence

For the focus accession on as_of_date, active_restrictions lists one row per restriction level among non-expired rows.

Lower precedence integer is stricter and wins for that level. Ignore expired rows where expires < as_of_date.
Sort output by level ascending.

When higher precedence integers are retained, active_restrictions reports the looser restriction for a level even though a stricter unexpired row exists. This is a museum rights-stack selection incompleteness, separate from dataset pin binding checks.
