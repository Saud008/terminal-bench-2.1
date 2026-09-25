use cose_audit::errors::AuditError;
use cose_audit::export::export_manifest;
use cose_audit::ingest::run_ingest;
use std::env;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        usage();
    }
    match args[1].as_str() {
        "ingest" => {
            let input = flag(&args, "--input").unwrap_or_else(|| usage());
            let ledger = flag(&args, "--ledger").unwrap_or_else(|| usage());
            let staging = flag(&args, "--staging").unwrap_or_else(|| usage());
            if let Err(e) = run_ingest(&input, &ledger, &staging) {
                eprintln!("{e}");
                process::exit(1);
            }
        }
        "export" => {
            let ledger = flag(&args, "--ledger").unwrap_or_else(|| usage());
            let staging = flag(&args, "--staging").unwrap_or_else(|| usage());
            let manifest = flag(&args, "--manifest").unwrap_or_else(|| usage());
            let _ = staging;
            let ledger_db = cose_audit::ledger::Ledger::open(&ledger);
            match ledger_db {
                Ok(db) => match export_manifest(&db, &manifest) {
                    Ok(_) => {}
                    Err(AuditError::EmptyLedger) => process::exit(2),
                    Err(e) => {
                        eprintln!("{e}");
                        process::exit(1);
                    }
                },
                Err(e) => {
                    eprintln!("{e}");
                    process::exit(1);
                }
            }
        }
        _ => usage(),
    }
}

fn flag(args: &[String], name: &str) -> Option<String> {
    args.iter()
        .position(|a| a == name)
        .and_then(|i| args.get(i + 1))
        .cloned()
}

fn usage() -> ! {
    eprintln!("usage: cose-audit ingest|export ...");
    process::exit(1);
}
