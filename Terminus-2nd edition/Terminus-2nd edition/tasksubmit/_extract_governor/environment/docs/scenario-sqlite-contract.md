# SQLite scenario contract

Each scenario directory contains library.db and meta.json.

Tables:

- scenario_meta(scenario, reconcile_date, catalog_seed)
- branches(branch_id, name, allows_interbranch_transfer)
- patrons(patron_id, home_branch_id, priority_class)
- hold_requests(request_id, patron_id, item_id, pickup_branch_id, hold_date)
- item_copies(copy_id, item_id, branch_id, status)
- suspension_windows(patron_id, start_date, end_date)
- priority_policies(class_name, rank)

Copy status available means status is exactly available.
