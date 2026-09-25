# SQLite scenario contract

Each scenario directory contains venue.db and meta.json.

Tables:

- scenario_meta(scenario, event_clock, catalog_seed)
- sections(section_id, name, row_count, accessibility_min)
- seats(seat_id, section_id, row_num, seat_num, accessible)
- orders(order_id, patron_id, payment_rank, captured_at)
- seat_holds(hold_id, order_id, seat_id, expires_at, status)

Hold status active means status is exactly active.
