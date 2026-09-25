# Overlap resolution

Within each document and label, spans overlap when start < other.end and other.start < end.

Group overlapping spans. For each group, select the winner span boundaries from the annotator with the highest weight in that group. Tie-break by longer span length, then lexicographic source span id.

Locked spans from adjudication locks are excluded from overlap merging and must appear verbatim in consensus output. Unlocked spans that overlap a locked span are discarded before overlap groups form.
