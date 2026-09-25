A quarry compliance crew must certify blast-induced ground vibration through numerical correlation of seismograph peaks, blast epicenters, and parcel boundary anchors. Implement seismocomply on the working Rust baseline under /app so operators can apply per-sensor calibration curves, compute closure between attenuated and corrected PPV values, group exceedances by property parcel boundaries, and select day versus night regulatory ceilings from jurisdiction tables.

The CLI loads mine-site survey JSON from /app/fixtures/surveys/, persists a seed-scoped peak correlation buffer at /app/state/peak-correlation-buffer.json, records the latest audit passport in /app/work/audit-passport.json, and publishes a regulatory exceedance atlas to a caller-provided path under /app/output/.

Install seismocomply at /app/bin/seismocomply from /app with these subcommands:

  seismocomply load-survey --seed <seed> --survey <name>
  seismocomply correlate --seed <seed> --survey <name>
  seismocomply publish-atlas --seed <seed> --survey <name> --output <path>

The peak correlation buffer written by load-survey must follow /app/docs/peak-correlation-buffer-schema.md. Distance attenuation from blast epicenter to each property compliance anchor uses /app/docs/distance-attenuation-contract.md. Sensor gain and zero-offset calibration for seismograph peaks follows /app/docs/sensor-calibration-contract.md. Property boundary grouping and the compliance anchor point for each parcel follows /app/docs/boundary-anchor-contract.md. Day versus night regulatory limit selection follows /app/docs/regulatory-threshold-contract.md with the survey timezone offset.

seismocomply correlate persists the active audit passport row for a seed and survey into /app/work/audit-passport.json. A later correlate pass for the same seed replaces the prior active row even when the survey name changes. Active-row semantics and audit_run_id format appear in /app/docs/audit-passport-schema.md.

seismocomply publish-atlas reads the peak correlation buffer together with the active audit passport row and writes exceedance atlas JSON to the caller-provided --output path. Row ordering, summary counters, and atlas_digest rules appear in /app/docs/atlas-publish-fields.md.

Bundled surveys and seeds live under /app/fixtures/. The bundled inventory and the behaviors each survey exercises appear in /app/docs/survey-inventory.md. Runtime-supplied survey overlays and limit scale adjustments follow those same contracts. Pytest harness behavior appears in /app/docs/verifier-harness-contract.md. Verifier modules /tests/seismocomply_contract_math.py and /tests/seismocomply_cli_support.py use hashlib, math, and random. Hidden survey tb3-night-scale and seed tb3-scale appear in survey-inventory.md.

Compile seismocomply with /usr/local/cargo/bin/cargo build --release --locked from /app and install the binary to /app/bin/seismocomply from /app/target/release/seismocomply. Run /app/scripts/clear-seismo-run.sh before cross-run verifier cases. The waveform decoy module is not used by load-survey, correlate, or publish-atlas.
