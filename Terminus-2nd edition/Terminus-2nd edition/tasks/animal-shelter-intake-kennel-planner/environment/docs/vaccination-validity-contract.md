# Vaccination eligibility window

Before weave assigns a kennel, VaccineEligible compares days remaining between intake_date and vacc_valid_until against min_valid_days from vaccination_policies for the arrival species.

Eligible when remaining days is greater than or equal to min_valid_days. Ineligible arrivals route to partner-shelter transfer selection without occupying on-site kennels.
