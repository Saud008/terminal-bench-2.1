Build debpol, a Debian APT install-candidate resolver for deb822-format source stanzas on the working Bash baseline under /app. debpol simulates offline apt policy without invoking apt: it ranks deb822 origins by Default-Pin, matches preferences Pin and Pin-Priority globs against offline index rows, compares dpkg revision strings including colon-prefix and tilde segments, filters by CPU architecture eligibility, and reports which package revision would become the install candidate for each query package.

debpol build-policy loads scenario bundles from /app/fixtures/scenarios/ into deb822-policy-graph.json at /app/state/deb822-policy-graph.json. debpol candidate-report writes install-candidate explanation JSON under /app/output/ without re-reading index files. Pin-priority tie rows remain pending until dpkg revision compare selects the published install candidate.

Install debpol at /app/bin/debpol with these subcommands:

  debpol build-policy --scenario <name> --run-id <id>
  debpol candidate-report --run-id <id> --output <path>

Deb822 stanza layout, continuation lines, and bundled scenario inventory appear in /app/docs/deb822-stanza-format.md. Origin ranking among enabled stanzas and Default-Pin ordering follow /app/docs/origin-ranking-rules.md. Pin and Pin-Priority glob matching follow /app/docs/pin-priority-rules.md. Dpkg revision ordering including colon-prefix and tilde segments follow /app/docs/dpkg-version-order.md. Architecture eligibility for candidates follows /app/docs/cpu-arch-gate-rules.md. Suite bias notes for scenarios appear in /app/docs/suite-bias-notes.md. Install candidate priority order and tie-break rules appear in /app/docs/apt-candidate-resolution.md. Verifier overlay scratch paths appear in /app/docs/verifier-overlay-paths.md.

debpol build-policy materializes deb822-policy-graph.json for a run id. Graph schema, origin_fingerprint, and digest rules appear in /app/docs/policy-graph-schema.md. debpol candidate-report reads the graph snapshot only and emits sorted install-candidate rows plus audit_digest. Report field rules and re-export output examples such as /app/output/run-alpha-reexport.json appear in /app/docs/candidate-report-fields.md.

Bundled scenarios live under /app/fixtures/scenarios/. Pytest helpers in tests/aptpol_runner.py invoke debpol through subprocess. Independent contract math lives in tests/aptpol_contract_math.py using fnmatch and hashlib per /app/tools/policy_primitives.py. Run /app/scripts/reset-state.sh before cross-run verifier cases. A release_label_sort decoy module exists off the build and report hot path.
