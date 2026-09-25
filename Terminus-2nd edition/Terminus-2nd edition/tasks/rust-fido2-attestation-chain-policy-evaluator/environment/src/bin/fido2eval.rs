        use fido2_attestation_evaluator::decode_bundle;
        use fido2_attestation_evaluator::cache_batch;
        use fido2_attestation_evaluator::attest_model::Config;
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
            match args[1].as_str() {
                "run-batch" => run_batch(&cfg, &args),
                _ => {
                    usage();
                    Err(2)
                }
            }
        }

        fn load_config() -> Result<Config, i32> {
            let raw = fs::read_to_string("/app/config/fido2eval.json").map_err(|e| {
                eprintln!("{e}");
                1
            })?;
            serde_json::from_str(&raw).map_err(|e| {
                eprintln!("{e}");
                1
            })
        }

        fn usage() {
            eprintln!("usage: fido2eval run-batch --batch <id> --bundle <name> --policy <name> --output <path>");
        }

        fn run_batch(cfg: &Config, args: &[String]) -> Result<(), i32> {
            let mut batch = String::new();
            let mut bundle = String::new();
            let mut policy = String::new();
            let mut output = String::new();
            let mut i = 2;
            while i < args.len() {
                match args[i].as_str() {
                    "--batch" if i + 1 < args.len() => {
                        batch = args[i + 1].clone();
                        i += 2;
                    }
                    "--bundle" if i + 1 < args.len() => {
                        bundle = args[i + 1].clone();
                        i += 2;
                    }
                    "--policy" if i + 1 < args.len() => {
                        policy = args[i + 1].clone();
                        i += 2;
                    }
                    "--output" if i + 1 < args.len() => {
                        output = args[i + 1].clone();
                        i += 2;
                    }
                    _ => {
                        usage();
                        return Err(2);
                    }
                }
            }
            if batch.is_empty() || bundle.is_empty() || policy.is_empty() || output.is_empty() {
                eprintln!("--batch, --bundle, --policy, and --output required");
                return Err(2);
            }
            let path = decode_bundle::bundle_path(&bundle);
            let bf = decode_bundle::load_bundle(&path).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
            if bf.batch_id != batch {
                eprintln!("batch_id mismatch");
                return Err(1);
            }
            cache_batch::write_snapshot(cfg, &batch, &bundle, &bf).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
            cache_batch::bind_policy(cfg, &batch, &policy).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
            let rep = fido2_attestation_evaluator::trust_emit::build_report(cfg, &batch).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
            write_trust(&PathBuf::from(output), &rep).map_err(|e| {
                eprintln!("{e}");
                1
            })
        }

        fn write_trust(path: &PathBuf, rep: &fido2_attestation_evaluator::attest_model::TrustReport) -> Result<(), String> {
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
            }
            let data = serde_json::to_string_pretty(rep).map_err(|e| e.to_string())?;
            std::fs::write(path, format!("{data}
")).map_err(|e| e.to_string())
        }
