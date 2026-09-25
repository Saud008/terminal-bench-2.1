# Scenario catalog

Bundled scenarios under /app/fixtures/scenarios/:

| Scenario | Exercises |
|----------|-----------|
| linear-chain | Three-block chain; possession on head conflicts with reservation on tail via zone reachability |
| diamond-fork | Fork yard; wing possessions conflict with combine-point reservation |
| signal-adjacent | restrict aspect on middle block blocks reservation using adjacent protected zone |
| crisis-override | priority-0 override suppresses possession versus reservation overlap |
| half-open-edge | touching half-open endpoints must not create a conflict |
| multi-possession-group | stable sorted group_key and sorted participant ids |

Hidden verifier scenario tb3-fork-reach lives under /opt/verifier-fixtures/railpos/scenarios/ when TB3_SCENARIO_DIR overrides the default scenario root.

Hidden verifier scenario tb3-override-zone tests zone-based override suppression on a three-block line.
