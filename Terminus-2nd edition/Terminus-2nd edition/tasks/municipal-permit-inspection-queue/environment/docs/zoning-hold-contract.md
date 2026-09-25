# Zoning hold contract

Active holds carry hold_rank per district. Higher hold_rank wins when multiple holds apply to the same district.

When any active hold rank is positive for a district, all permits in that district are hold_blocked during score-queue and receive composite_score zero.

hold-mask.json maps district_id to the winning hold_rank.
