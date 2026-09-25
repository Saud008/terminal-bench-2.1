# Lot certificate hash

cert_digest for each lot is the first 16 hex chars of SHA-256 over UTF-8 lot_id colon as_of_date colon assay_code in that order. Assay code is never prefixed before lot_id.
