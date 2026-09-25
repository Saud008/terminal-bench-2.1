use witness_ledger::{
    DEFAULT_LEDGER_PATH, DEFAULT_STAGING_PATH, DEFAULT_VERDICT_PATH,
};

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
    match args[1].as_str() {
        "load" => {
            if args.len() != 3 {
                eprintln!("usage: twctl load <bundle-dir>");
                return Err(2);
            }
            witness_ledger::bundle::load_bundle_dir(&args[2], DEFAULT_STAGING_PATH).map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        "check" => {
            let mut epoch: Option<u64> = None;
            let mut staging = DEFAULT_STAGING_PATH.to_string();
            let mut i = 2;
            while i < args.len() {
                match args[i].as_str() {
                    "--epoch" if i + 1 < args.len() => {
                        epoch = Some(args[i + 1].parse().map_err(|_| 2)?);
                        i += 2;
                    }
                    "--staging" if i + 1 < args.len() => {
                        staging = args[i + 1].clone();
                        i += 2;
                    }
                    _ => return Err(2),
                }
            }
            let Some(epoch) = epoch else {
                eprintln!("twctl check: --epoch required");
                return Err(2);
            };
            let effective = apply_epoch_bias(epoch);
            witness_ledger::quorum::eval_quorum_at_epoch(&staging, effective, DEFAULT_VERDICT_PATH)
                .map_err(|e| {
                    eprintln!("{e}");
                    1
                })?;
        }
        "emit" => {
            witness_ledger::emit::emit_release_ledger(
                DEFAULT_STAGING_PATH,
                DEFAULT_VERDICT_PATH,
                DEFAULT_LEDGER_PATH,
            )
            .map_err(|e| {
                eprintln!("{e}");
                1
            })?;
        }
        _ => {
            usage();
            return Err(2);
        }
    }
    Ok(())
}

fn apply_epoch_bias(epoch: u64) -> u64 {
    std::env::var("TB3_EPOCH_BIAS")
        .ok()
        .and_then(|v| v.parse::<u64>().ok())
        .map(|bias| epoch.saturating_add(bias))
        .unwrap_or(epoch)
}

fn usage() {
    eprintln!("usage: twctl load <dir> | twctl check --epoch <n> [--staging <path>] | twctl emit");
}
