# Accession ops workflow — museum vault playtest

This task is a **games** museum accession vault playtest (admit → gate → seal). The playfield admits offline archive packs into a seed-scoped vault, enforces custody-lineage, loan-window, rights-precedence, restoration-chronology, and duplicate-accession traps during compose align, then seals dossier JSON from the active register row only when the dossier win condition holds. The working baseline under /app must keep vault admission, register supersession barriers, and sealed dossier export aligned; it is not a Python package rebuild, pytest harness, or service-repair exercise.

There is no remote museum CMS. Playtest verbs are vault load (admit + materialize), compose align (apply gates into register.db), and publish dossier (seal compliance JSON from the matching vault and active register row).

Published `custody_lineage` is an ordered list of party name strings (earliest `from_party`, then each `to_party` by `transfer_date`; same-date rows keep archive input order). It is not `"A to B"` edge strings. See custody-lineage-contract.md.

After playfield policy edits under `/app/lib/musdoss/`, leave `/usr/local/bin/musdoss` current. Before grading, the verifier invokes `/app/scripts/verifier-rebuild.sh`.
