# Registry SQLite layout

Each scenario folder ships registry.sqlite plus arrivals.jsonl and meta.json.

Tables:

- scenario_meta(scenario, intake_date, catalog_seed)
- species_profiles(species_code, name, isolation_rank)
- kennels(kennel_id, species_code, capacity, zone)
- quarantine_windows(kennel_id, start_date, end_date)
- vaccination_policies(species_code, min_valid_days)
- kennel_compat_rules(from_species, to_species)
- transfer_penalties(from_species, to_species, transfer_penalty)
- adoption_holds(hold_type, precedence_rank)

Arrival animals are not stored in registry.sqlite; they arrive via arrivals.jsonl at bind time.
