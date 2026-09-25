# Payment precedence contract

Lower payment_rank integer means higher capture priority.

Within the same rank, earlier captured_at wins. Tie-break order_id ascending.
