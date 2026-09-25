# Certificate authority scope

When signed_by_ca is true, the signing ca_id must exist in the trust ledger cas array. The requested principal must appear in principals_allowed for that CA unless principals_allowed is the wildcard star.

CA principal lists use comma separation inside the principals option on cert-authority lines.
