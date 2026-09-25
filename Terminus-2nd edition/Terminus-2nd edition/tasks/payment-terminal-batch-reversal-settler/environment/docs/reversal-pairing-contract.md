# Reversal pairing contract

Reversal transcripts must link to an originating sale via links_sale_id matching the sale txn_id on the same terminal_id with the same lowercase auth_code and amount_cents.

Pairing is evaluated over the full normalized transcript set using those linkage fields only. A linked reversal must pair when terminal_id, lowercase auth_code, amount_cents, and links_sale_id match the sale — even if the reversal appears before its sale in the transcript array, and even if the reversal's event_ms is earlier than the sale's event_ms. Do not reject a linked reversal solely because of transcript array order or event_ms ordering between the pair.

event_ms ordering applies only when emitting journal rows per batch-journal-contract.md; it is not a pairing eligibility gate.

When pairing succeeds the sale state becomes settled and the reversal state becomes reversal_applied.

Sales that remain in captured state after reversal pairing and cutoff filtering finalize to settled before journal emission per batch-journal-contract.

Unmatched reversals receive state reversal_rejected and do not reduce net_amount_cents.

Auth codes are normalized to lowercase before comparison and digest computation.
