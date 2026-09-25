Task identity 64a78d5bc1 defines the engineering problem for bash kernel kconfig fragment attestor. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Build kcfgattest, a kernel configuration fragment attestor on the working Bash baseline under /app. kcfgattest merges a defconfig base with ordered fragment files, applies dependency-implied symbol closure, evaluates policy constraints, and emits a reproducible merged configuration manifest with audit digests. The tool operates offline on fixture bundles without invoking the real kernel build.

kcfgattest compile-stage loads a bundle from /app/fixtures/bundles/ into kcfg-stage.json at /app/state/kcfg-stage.json; kcfgattest emit-manifest reads the stage snapshot only and writes manifest JSON under /app/output without re-parsing defconfig or fragment sources from disk.

Install kcfgattest at /app/bin/kcfgattest with these subcommands:

  kcfgattest compile-stage --bundle NAME --run-id ID
  kcfgattest emit-manifest --run-id ID --output PATH

Kconfig assignment syntax, unset lines, and bundled bundle inventory appear in /app/docs/kconfig-syntax.md. Fragment basename ordering and override precedence among layers follow /app/docs/fragment-ordering.md. Requires, implies, and selects dependency closure rules follow /app/docs/dependency-imply-rules.md. Forbidden symbols, required-n constraints, and modular caps follow /app/docs/policy-constraints.md. Stage snapshot schema, stage_digest, and cross-run replay notes appear in /app/docs/staging-schema.md. Manifest symbol rows, source_layer values, violation codes, and manifest_digest rules appear in /app/docs/manifest-fields.md.

kcfgattest compile-stage materializes kcfg-stage.json for a run id at /app/state/kcfg-stage.json before emit-manifest produces sorted symbol rows plus policy_violations and manifest_digest under /app/output. Cross-run tests use run ids such as run-bravo and run-alpha. module-policy bundle exercises CONFIG_DEBUG_KERNEL forbidden_set when assigned modular value m.

Bundled bundles live under /app/fixtures/bundles/. Pytest helpers in tests/kcfg_runner.py invoke kcfgattest through subprocess. Independent contract math lives in tests/kcfg_contract_math.py using hashlib digests aligned with /app/tools/kcfg_primitives.py. Run /app/scripts/reset-state.sh before cross-run verifier cases. The decoy sort helper is not used by compile-stage ingest or emit-manifest export.
