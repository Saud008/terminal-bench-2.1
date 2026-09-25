# Adjudication locks

Annotators with adjudicator true may declare locks in annotation files. Locks declared by non-adjudicator annotators must be ignored. A span lock references doc_id and span_id. Locked spans must appear in consensus with locked true and must not be removed by overlap resolution, even when a higher-weight unlocked span overlaps them.

Apply lock precedence before overlap merging: locked spans are copied directly; unlocked spans that overlap any locked span are discarded; only the remaining unlocked spans participate in overlap groups.
