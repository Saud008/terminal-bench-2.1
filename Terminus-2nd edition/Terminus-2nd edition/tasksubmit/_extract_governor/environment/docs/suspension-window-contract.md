# Suspension window contract

Patron holds are skipped when reconcile_date falls inside any suspension window for that patron.

Inclusive bounds: start_date <= reconcile_date <= end_date blocks the patron.
