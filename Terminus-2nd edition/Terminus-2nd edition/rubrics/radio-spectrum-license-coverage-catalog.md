# Platform rubric — radio-spectrum-license-coverage-catalog

**Task folder:** tasks/radio-spectrum-license-coverage-catalog/

Agent binds transmitter sites to declared license_id grants after band and bbox containment checks, +3
Agent selects highest numeric priority grant when license_id is empty on overlapping coverage, +3
Agent treats license renewal_date >= bundle as_of_date as valid and drops expired sites, +3
Agent marks sites excluded=true when coordinates fall inside same-band exclusion zones, +3
Agent counts touching MHz band intervals as overlap peers per catalog-export-fields, +2
Agent increments load_generation on each prepare-atlas pass for the same seed, +2
Agent writes atlas_seq_id from seed bundle and load_generation per coverage-generation-schema, +2
Agent sorts atlas rows by holder then band_id then site_id ascending, +2
Agent computes audit_digest from summary counters not raw row ordering alone, +2
Agent honors inclusive bbox max edges for boundary transmitter sites, +2
Agent applies TB3_FIXTURE_DIR hidden bundle overlays without bundled fixture drift, +2
Agent patches geo containment only while leaving priority ranking inverted on empty license_id, -3
Agent treats overlapping bands as disjoint by excluding touching MHz intervals, -3
Agent binds lowest priority grant when multiple licenses cover one site, -3
Agent inverts exclusion flags marking non-excluded sites inside exclusion zones, -3
Agent keeps expired licenses active by comparing renewal_date with strict greater-than, -3
Agent skips load_generation advance allowing stale atlas_seq_id after recompile, -2
