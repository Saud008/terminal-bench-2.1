mod cbor;
mod db;
mod export;
mod ingest;
mod model;
mod sign;
mod staging;

use std::env;
use std::path::PathBuf;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: cbor-audit <ingest|export> ...");
        process::exit(2);
    }
    let result = match args[1].as_str() {
        "ingest" => run_ingest(&args[2..]),
        "export" => run_export(&args[2..]),
        _ => {
            eprintln!("unknown subcommand: {}", args[1]);
            process::exit(2)
        }
    };
    if let Err(err) = result {
        eprintln!("error: {}", err);
        process::exit(1);
    }
}

fn run_ingest(args: &[String]) -> Result<(), String> {
    let mut bundle = None;
    let mut revalidate = false;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--bundle" => {
                i += 1;
                bundle = Some(PathBuf::from(args.get(i).ok_or("missing --bundle")?));
            }
            "--revalidate" => {
                revalidate = true;
            }
            other => return Err(format!("unknown flag: {}", other)),
        }
        i += 1;
    }
    let path = bundle.ok_or("--bundle required")?;
    ingest::run(&path, revalidate)
}

fn run_export(args: &[String]) -> Result<(), String> {
    let mut report = PathBuf::from("/app/output/attestation.json");
    let mut ingest_src = None;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--report" => {
                i += 1;
                report = PathBuf::from(args.get(i).ok_or("missing --report")?);
            }
            "--ingest-source" => {
                i += 1;
                ingest_src = Some(PathBuf::from(args.get(i).ok_or("missing --ingest-source")?));
            }
            other => return Err(format!("unknown flag: {}", other)),
        }
        i += 1;
    }
    export::sign::run(&report, ingest_src.as_deref())
}
