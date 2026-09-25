# Visa overlap contract

A visa is usable only when its entire validity span fits inside the linked passport window:

passport.issue_date <= visa.valid_from and visa.valid_to <= passport.expiry_date (inclusive).

The reference_date must also fall inside visa.valid_from .. visa.valid_to inclusive.

Deny reason token: visa_overlap when containment fails.
