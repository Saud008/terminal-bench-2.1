# Night scenario SQLite layout

Each scenario folder ships hotel.db plus meta.json under the fixtures tree.

Tables:

- scenario_meta(scenario, night_date, catalog_seed)
- room_types(room_type_id, name, rank)
- rooms(room_id, room_type_id, status)
- reservations(reservation_id, guest_id, room_type_id, loyalty_tier, cancel_prob, arrival_rank)
- maintenance_windows(room_id, start_date, end_date)
- loyalty_policies(tier_name, protection_rank)
- substitution_rules(from_type_id, to_type_id)
- walk_costs(from_type_id, to_type_id, cost_cents)

build_scenarios.py derives guest and room identifiers from a scenario-name hash so tests resist hard-coded ids.
