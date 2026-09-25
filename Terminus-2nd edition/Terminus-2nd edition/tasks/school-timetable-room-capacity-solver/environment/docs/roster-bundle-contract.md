# Roster bundle contract

Each scenario directory contains bundle.json with keys: seed, sections, teachers, rooms, slots, policies.

Sections include section_id, course_id, teacher_id, enrolled, requires_lab, split_group, preferred_slots.

Anti-hardcoding: build_scenarios.py randomizes display names using seed but preserves constraint topology via stable ids in bundle.json.
