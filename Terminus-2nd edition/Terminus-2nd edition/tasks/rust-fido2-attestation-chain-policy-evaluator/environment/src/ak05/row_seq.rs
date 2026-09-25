        use crate::registry_aaguid;
        use crate::crypto_authdata;
        use crate::crypto_x509;
        use crate::attest_model::{
            BundleFile, Config, PolicyActive, PolicyBind, TranscriptCache, TranscriptRow,
        };
        use std::fs;
        use std::path::Path;

        pub fn write_snapshot(cfg: &Config, batch: &str, bundle: &str, bf: &BundleFile) -> Result<(), String> {
            let reg = registry_aaguid::load_registry(&crate::metadata_path(cfg))?;
            let mut rows = Vec::new();
            for tr in &bf.transcripts {
                let bytes = hex::decode(&tr.auth_data_hex).map_err(|e| e.to_string())?;
                let (uv, sign_count, raw_aaguid) = crypto_authdata::parse_auth_data(&bytes)?;
                let parsed_aaguid = crypto_authdata::aaguid_to_string(raw_aaguid);
                let chain_ok = crypto_x509::chain_valid(&tr.cert_chain);
                let metadata_hit = registry_aaguid::lookup(&reg, &parsed_aaguid).is_some()
                    || registry_aaguid::lookup(&reg, &tr.aaguid).is_some();
                rows.push(TranscriptRow {
                    credential_id: tr.credential_id.clone(),
                    aaguid: tr.aaguid.clone(),
                    attestation_format: tr.attestation_format.clone(),
                    auth_data_hex: tr.auth_data_hex.clone(),
                    sign_count,
                    cert_chain: tr.cert_chain.clone(),
                    uv,
                    chain_ok,
                    metadata_hit,
                });
            }
            let snap = TranscriptCache {
                run_seq: 0,
                batch_id: batch.to_string(),
                bundle: bundle.to_string(),
                rows,
            };
            write_json(&cfg.transcript_cache_path, &snap)
        }

        pub fn read_snapshot(path: &str) -> Result<TranscriptCache, String> {
            let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
            serde_json::from_str(&raw).map_err(|e| e.to_string())
        }

        pub fn bind_policy(cfg: &Config, batch: &str, policy_name: &str) -> Result<(), String> {
            let snap = read_snapshot(&cfg.transcript_cache_path)?;
            if snap.batch_id != batch {
                return Err("batch mismatch".into());
            }
            let active = PolicyActive {
                batch_id: batch.to_string(),
                policy_name: policy_name.to_string(),
                bind_seq: snap.run_seq,
            };
            write_policy_bind(&cfg.policy_bind_path, active)
        }

        pub fn read_active_policy(cfg: &Config) -> Result<PolicyActive, String> {
            let ledger = read_policy_bind(&cfg.policy_bind_path)?;
            ledger.active.ok_or_else(|| "no active policy".into())
        }

        fn write_json(path: &str, v: &TranscriptCache) -> Result<(), String> {
            if let Some(parent) = Path::new(path).parent() {
                fs::create_dir_all(parent).map_err(|e| e.to_string())?;
            }
            let data = serde_json::to_string_pretty(v).map_err(|e| e.to_string())?;
            fs::write(path, format!("{data}
")).map_err(|e| e.to_string())
        }

        fn read_policy_bind(path: &str) -> Result<PolicyBind, String> {
            if !Path::new(path).exists() {
                return Ok(PolicyBind { active: None });
            }
            let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
            serde_json::from_str(&raw).map_err(|e| e.to_string())
        }

        fn write_policy_bind(path: &str, active: PolicyActive) -> Result<(), String> {
            if let Some(parent) = Path::new(path).parent() {
                fs::create_dir_all(parent).map_err(|e| e.to_string())?;
            }
            let ledger = PolicyBind { active: Some(active) };
            let data = serde_json::to_string_pretty(&ledger).map_err(|e| e.to_string())?;
            fs::write(path, format!("{data}
")).map_err(|e| e.to_string())
        }
