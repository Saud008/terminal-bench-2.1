# Compile contract

zonefrag compile --tree DIR --seed SEED --output FILE.json runs ingest to a internal snapshot then export.

Optional --reload applies serial-policy.md bump during ingest.

compile must produce byte-identical output to ingest followed by export when using the same snapshot path semantics.

Subcommand verify reads snapshot JSON only and prints ok/issues JSON to stdout.
