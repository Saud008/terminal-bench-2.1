# s6-rc bundle resolver

The s6-bundle-resolver driver under /app/bin ingests s6-rc bundle definitions, validates dependency graphs, plans startup order, checks longrun readiness against mock rc state, applies transitions through s6_rc_mock.py, and exports the effective service graph.

Contract documents live under /app/docs/. Bundle fixtures under /app/fixtures/ are read-only inputs.
