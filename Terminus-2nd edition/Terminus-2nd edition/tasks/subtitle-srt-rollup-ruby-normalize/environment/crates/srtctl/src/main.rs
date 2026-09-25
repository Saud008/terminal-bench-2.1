use std::env;
use std::path::PathBuf;
use std::process;

use srt_core::normalize;

fn usage() -> ! {
    eprintln!("usage: srtctl normalize --in <path> --seed <seed> --fixture <name> --export <json>");
    process::exit(2);
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        usage();
    }

    match args[1].as_str() {
        "normalize" => run_normalize(&args[2..]),
        _ => usage(),
    }
}

fn run_normalize(args: &[String]) {
    let mut input: Option<PathBuf> = None;
    let mut seed: Option<String> = None;
    let mut fixture: Option<String> = None;
    let mut export: Option<PathBuf> = None;

    let mut idx = 0;
    while idx < args.len() {
        match args[idx].as_str() {
            "--in" => {
                idx += 1;
                input = Some(PathBuf::from(args.get(idx).unwrap_or_else(|| usage())));
            }
            "--seed" => {
                idx += 1;
                seed = Some(args.get(idx).unwrap_or_else(|| usage()).clone());
            }
            "--fixture" => {
                idx += 1;
                fixture = Some(args.get(idx).unwrap_or_else(|| usage()).clone());
            }
            "--export" => {
                idx += 1;
                export = Some(PathBuf::from(args.get(idx).unwrap_or_else(|| usage())));
            }
            other => {
                eprintln!("unknown argument: {other}");
                usage();
            }
        }
        idx += 1;
    }

    let input = input.unwrap_or_else(|| usage());
    let seed = seed.unwrap_or_else(|| usage());
    let fixture = fixture.unwrap_or_else(|| usage());
    let export = export.unwrap_or_else(|| usage());

    let doc = normalize(&input, &seed, &fixture);
    let json = serde_json::to_string_pretty(&doc).expect("serialize export");
    std::fs::write(&export, json).expect("write export");
}
