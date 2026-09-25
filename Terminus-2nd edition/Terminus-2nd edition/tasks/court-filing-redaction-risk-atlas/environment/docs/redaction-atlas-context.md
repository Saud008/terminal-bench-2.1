# Court filing sealed-disclosure context

This environment is a **security** sealed-record disclosure gate: detect sealed-term exposure, party-alias bypass, and exhibit cross-reference leakage before public docket release.

## Domain vocabulary

| Term | Meaning |
|------|---------|
| Filing bundle | Scenario inputs: dockets, parties, paginated text, sealed term list, policy |
| Party alias graph | Directed alias edges between party ids and name strings with reachability expansion |
| Exhibit sub-reference | Exhibit label with suffix such as Exhibit 12-A or roman numeral attachment |
| Sealed term | Token from sealed_terms.json that must not appear in public filing text |
| Page-line citation | Page number and 1-based line index where sealed or party-linked text appears |
| Primary docket | Docket row marked primary_flag=true when duplicates share a matter |
| Redaction-risk atlas | Digest-sealed JSON listing scored disclosure findings with party, exhibit, docket, and citation fields |

## Security workflow

Operators bind a scenario bundle, index parties to expand alias reachability, scan paginated filing lines under sealed policy, then emit an atlas for triage. Emission is gated on successful party indexing so alias-bypass findings cannot be omitted.

## Non-goals

No live PACER or CM/ECF integration. No OCR or PDF parsing. No machine-learning NER models. Matching uses deterministic string normalization and alias graph rules documented in contract files.
