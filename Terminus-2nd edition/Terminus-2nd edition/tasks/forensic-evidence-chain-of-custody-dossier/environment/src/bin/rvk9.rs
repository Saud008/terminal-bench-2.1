            use forensic_custody_dossier::custody_types::Config;
            use std::fs;
            use std::path::PathBuf;

            fn main() {
                if let Err(code) = run() {
                    std::process::exit(code);
                }
            }

            fn run() -> Result<(), i32> {
                let args: Vec<String> = std::env::args().collect();
                if args.len() < 2 {
                    usage();
                    return Err(2);
                }
                let cfg = load_config()?;
                match (args[1].as_str(), args.get(2).map(|s| s.as_str())) {
                    ("vault", Some("load")) => cmd_vault_load(&cfg, &args),
                    ("registry", Some("bind")) => cmd_registry_bind(&cfg, &args),
                    ("attest", Some("dossier")) => cmd_attest(&cfg, &args),
                    _ => {
                        usage();
                        Err(2)
                    }
                }
            }

            fn load_config() -> Result<Config, i32> {
                let raw = fs::read_to_string("/app/config/rvk9.json").map_err(|_| 1)?;
                serde_json::from_str(&raw).map_err(|_| 1)
            }

            fn usage() {
                eprintln!("usage: rvk9 vault load --case <id> --bundle <name>");
                eprintln!("       rvk9 registry bind --case <id> --bundle <name>");
                eprintln!("       rvk9 attest dossier --case <id> --bundle <name> --output <path>");
            }

            fn parse_flags(args: &[String], start: usize) -> Result<(String, String, Option<String>), i32> {
                let mut case_id = String::new();
                let mut bundle = String::new();
                let mut output = None;
                let mut i = start;
                while i < args.len() {
                    match args[i].as_str() {
                        "--case" if i + 1 < args.len() => {
                            case_id = args[i + 1].clone();
                            i += 2;
                        }
                        "--bundle" if i + 1 < args.len() => {
                            bundle = args[i + 1].clone();
                            i += 2;
                        }
                        "--output" if i + 1 < args.len() => {
                            output = Some(args[i + 1].clone());
                            i += 2;
                        }
                        _ => return Err(2),
                    }
                }
                if case_id.is_empty() || bundle.is_empty() {
                    return Err(2);
                }
                Ok((case_id, bundle, output))
            }

            fn cmd_vault_load(cfg: &Config, args: &[String]) -> Result<(), i32> {
                let (case_id, bundle, _) = parse_flags(args, 3)?;
                let path = forensic_custody_dossier::decode_bundle::bundle_path(&bundle);
                let bf = forensic_custody_dossier::decode_bundle::load_bundle(&path).map_err(|_| 1)?;
                forensic_custody_dossier::mod_a::vault_load(&case_id, &bf).map_err(|_| 1)?;
                Ok(())
            }

            fn cmd_registry_bind(cfg: &Config, args: &[String]) -> Result<(), i32> {
                let (case_id, bundle, _) = parse_flags(args, 3)?;
                let vault_raw =
                    fs::read_to_string("/app/var/custody-vault.json").map_err(|_| 1)?;
                let vault: forensic_custody_dossier::custody_types::VaultLedger =
                    serde_json::from_str(&vault_raw).map_err(|_| 1)?;
                if vault.case_id != case_id || vault.bundle_id != bundle {
                    return Err(1);
                }
                let path = forensic_custody_dossier::decode_bundle::bundle_path(&bundle);
                let bf = forensic_custody_dossier::decode_bundle::load_bundle(&path).map_err(|_| 1)?;
                let mut combined = bf.transfers.clone();
                combined.extend(bf.seal_checks.clone());
                forensic_custody_dossier::mod_g::reconcile(
                    &vault,
                    &combined,
                    &bf.exhibit_aliases,
                )
                .map_err(|_| 1)?;
                Ok(())
            }

            fn cmd_attest(cfg: &Config, args: &[String]) -> Result<(), i32> {
                let (case_id, bundle, output) = parse_flags(args, 3)?;
                let out = output.ok_or(2)?;
                let vault_raw =
                    fs::read_to_string("/app/var/custody-vault.json").map_err(|_| 1)?;
                let vault: forensic_custody_dossier::custody_types::VaultLedger =
                    serde_json::from_str(&vault_raw).map_err(|_| 1)?;
                let ledger_raw =
                    fs::read_to_string("/app/var/exhibit-register.json").map_err(|_| 1)?;
                let ledger: forensic_custody_dossier::custody_types::RegisterLedger =
                    serde_json::from_str(&ledger_raw).map_err(|_| 1)?;
                if vault.case_id != case_id
                    || vault.bundle_id != bundle
                    || ledger.ledger_seq != vault.run_seq
                {
                    return Err(1);
                }
                let rep = forensic_custody_dossier::mod_g::compile(
                    &vault,
                    &ledger,
                    &cfg.location_catalog,
                )
                .map_err(|_| 1)?;
                let path = PathBuf::from(out);
                if let Some(parent) = path.parent() {
                    fs::create_dir_all(parent).map_err(|_| 1)?;
                }
                fs::write(
                    &path,
                    format!(
                        "{}
",
                        serde_json::to_string_pretty(&rep).map_err(|_| 1)?
                    ),
                )
                .map_err(|_| 1)?;
                Ok(())
            }
