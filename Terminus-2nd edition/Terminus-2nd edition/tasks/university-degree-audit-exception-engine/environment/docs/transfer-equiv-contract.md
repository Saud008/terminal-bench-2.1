# Transfer articulation equivalence contract

Transfer transcript rows carry source course_code values from external institutions. Before requirement matching, map each transfer row through transfer_equivalence where the student locked catalog_year falls within valid_from_year through valid_to_year inclusive on both bounds.

When multiple articulation rows match, choose the row with the greatest valid_from_year, then smallest target_code lexicographically.

Mapped target_code replaces the transfer source for credit counting and department pool checks. Unmapped transfer rows contribute zero credits.

Articulation windows are catalog-year based, not enrollment term based.
