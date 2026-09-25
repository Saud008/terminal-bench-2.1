# Custody lineage contract

For the focus accession, `custody_lineage` is a JSON array of **party name strings** in custody order. Each element is a single custodian name (for example `"Gallery East"`), not a transfer edge string such as `"Gallery East to Conservation Lab"`.

Build the list as follows:

1. Include the `from_party` of the earliest transfer for the focus accession.
2. Append each transfer's `to_party` in `transfer_date` ascending order.
3. Transfers that share a `transfer_date` keep their archive input order (stable date sort). Do not alphabetize parties as a tie-break.

Ignore transfers for other accession ids. Do not sort party names lexicographically and do not emit `"from to to"` edge strings.

Example: three transfers `Donor → Registrar → Gallery → Lab` yields `["Donor", "Registrar", "Gallery", "Lab"]`.

When parties are sorted alphabetically or encoded as edge strings, provenance dossiers no longer match transfer chronology and break loan and rights adjudication.
