# Engineering problem contract

## Root cause envelope

Registrar timetable allocation fails when cohort sync, teacher-collision guards, lab-kind matching, room capacity saturation, and stable rank keys disagree across planner modules. Partial fixes leave double-booked teachers, lab sections in classrooms, or split cohorts on different periods.

## Failure modes verified

- split_group cohort drift assigns linked sections to different slot_id values
- teacher_collision allows duplicate teacher_id within one slot_id
- room_capacity treats rooms as exclusive instead of summing enrolled headcount
- lab_kind mismatch assigns requires_lab sections to non-lab room_kind rows
- rank_key tie-break uses teacher_id before section_id and scrambles atlas precedence
- constraint_graph omits lab_requirement edges for lab sections
- atlas_publish skips allocation_pass gate and writes before allocate-slots
- conflict_ledger drops teacher_double_book rows when collisions remain

## Domain traps

Hidden verifier bundles stress lab_kind capacity edges and cohort sync under TB3_SCORE_BIAS epsilon shifts. Reference math in ttalloc_refmath recomputes assignments independently from bundle.json facts.
