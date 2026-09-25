# Carrier ops failure modes — SIP dialog CDR

## Carrier billing context

VoIP carriers derive billable call-detail records by correlating offline SIP transcript legs: INVITE transactions, provisional responses such as 180 Ringing or 183 Session Progress, final 2xx answers, and teardown via CANCEL or BYE. Each billable leg is keyed by Call-ID plus To-tag after forking.

## Ops gate failures

| Gate | When policy is wrong |
|------|----------------------|
| To-tag omitted from branch join | Forked callee legs combine or the unanswered fork is rated |
| 183 Session Progress treated as answer | Ring-only dialogs appear as completed CDR |
| BYE wins over early CANCEL | Pre-answer cancel appears as a completed call in SQLite |
| SIP retransmissions not collapsed | Repeated 200 OK responses produce twin SQLite rows |
| clock_skew_ms not applied before rating | Peak versus offpeak tier follows uncorrected epoch values |
| Billing window end treated as exclusive | Last billable second inside the window is dropped |

## Observable failure modes

Double billing on forked To-tag branches, provisional-only rows in cdr.sqlite, canceled calls marked completed, inflated row counts after a retransmission storm, wrong billing tier after skew correction, and off-catalog traps that require TB3_FIXTURE_DIR transcripts.

## SIP concept anchors

Dialog branch join, provisional gating, terminate precedence, retransmission collapse, skew-adjusted rating, inclusive carrier billing minute, answered-dialog CDR filter, INVITE transaction, BYE teardown, CANCEL preemption, 183 Session Progress, 180 Ringing, To-tag fork, CSeq sort key, Call-ID correlation, carrier peak tariff, offpeak minute bucket.
