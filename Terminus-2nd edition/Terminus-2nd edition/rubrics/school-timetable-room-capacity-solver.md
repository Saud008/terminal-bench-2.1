# Platform rubric — school-timetable-room-capacity-solver

**Task folder:** tasks/school-timetable-room-capacity-solver/

Agent ingests roster bundle JSON into active-roster.json with scenario seed metadata, +2
Agent materializes constraint-graph.json with graph_fingerprint and lab requirement edges, +3
Agent groups split sections by split_group not course_id for synchronized slot_id, +3
Agent assigns lab-required sections only to rooms whose room_kind is lab, +3
Agent sums enrolled headcount per room and slot against capacity minus margin, +3
Agent blocks teacher_id from two assignments sharing the same slot_id, +3
Agent ranks ties by section_id then teacher_id then room_id then slot_id ascending, +3
Agent increments allocation_pass only after allocate-slots writes allocate-log.json, +2
Agent blocks publish-atlas until allocation_pass is greater than zero, +2
Agent emits teacher_double_book entries in conflict-report.json when violations occur, +2
Agent honors TB3_SCORE_BIAS on hidden lab trap stable score recomputation, +2
Agent rebuilds ttalloc via verifier-rebuild.sh before subprocess CLI verification, +2
Agent treats split_group empty string as no grouping and schedules independently, -2
Agent allows two sections in one room slot when combined enrolled exceeds capacity, -3
Agent schedules lab courses into classroom room_kind when capacity is higher, -3
Agent permits duplicate teacher_id assignments in the same slot_id, -3
Agent publishes timetable-atlas.json before allocate-slots increments allocation_pass, -3
