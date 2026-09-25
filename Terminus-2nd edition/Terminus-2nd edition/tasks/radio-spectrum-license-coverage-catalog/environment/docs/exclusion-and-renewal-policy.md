# Exclusion and renewal policy

Sites whose coordinates fall inside an exclusion zone for the same band_id are marked excluded=true in catalog rows. A license is valid on the bundle as_of_date when renewal_date >= as_of_date. Expired licenses drop their sites and increment summary.expired_dropped.
