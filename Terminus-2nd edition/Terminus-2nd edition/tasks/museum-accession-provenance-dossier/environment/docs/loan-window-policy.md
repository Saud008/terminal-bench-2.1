# Exhibition loan window policy

On this games museum accession playtest, for the focus accession flag loan_conflicts when:

- return_by is before as_of_date on the archive (missed return window)
- two loans overlap in time (loan_start..loan_end ranges intersect)

Reason codes: missed_return_window, overlapping_loan. Inclusive loan intervals
overlap even when one loan starts on the other loan's loan_end date.

Each emitted loan_conflicts row is exactly
{"accession_id":"<focus>","reason":"<code>"} - only accession_id and reason.
Do not attach loan calendar fields or other diagnostics to the row; dossier publish
compares the array with full JSON equality (see dossier-publish-fields.md).

For deterministic output, first sort focus-accession loans by
(loan_start, loan_end, return_by, borrower). Emit one missed_return_window row for
each sorted loan whose return_by is before as_of_date. Then emit one
overlapping_loan row for every overlapping pair in sorted pair order (i, j), i < j.
Thus all missed_return_window rows precede all overlapping_loan rows, and repeated
reason rows are significant.

When calendar overlap detection or return_by versus as_of_date checks are absent, loan_conflicts stays empty while overlapping exhibition windows exist. That is a museum loan-calendar incompleteness, separate from experiment pin binding checks.
