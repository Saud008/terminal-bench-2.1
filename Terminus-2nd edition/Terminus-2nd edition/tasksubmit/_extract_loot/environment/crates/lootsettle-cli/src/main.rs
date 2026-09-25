use std::env;
use std::path::PathBuf;
use std::process;

use lootsettle_core::{run_export, run_ingest, run_replay, run_settle, write_report};

fn main() {
    let mut args = env::args().skip(1);
    let cmd = args.next().unwrap_or_else(|| usage());
    match cmd.as_str() {
        "ingest" => run_ingest_cmd(&mut args),
        "settle" => run_settle_cmd(&mut args),
        "export" => run_export_cmd(&mut args),
        "replay" => run_replay_cmd(&mut args),
        _ => usage(),
    }
}

fn run_ingest_cmd(args: &mut impl Iterator<Item = String>) {
    let opts = parse_replay_flags(args);
    run_ingest(&opts.season, &opts.events).unwrap_or_else(|e| {
        eprintln!("ingest failed: {e}");
        process::exit(1);
    });
}

fn run_settle_cmd(args: &mut impl Iterator<Item = String>) {
    let mut seasons_dir = PathBuf::from("/app/fixtures/seasons");
    while let Some(flag) = args.next() {
        match flag.as_str() {
            "--seasons-dir" => {
                seasons_dir = PathBuf::from(args.next().expect("--seasons-dir value"));
            }
            _ => usage(),
        }
    }
    run_settle(&seasons_dir).unwrap_or_else(|e| {
        eprintln!("settle failed: {e}");
        process::exit(1);
    });
}

fn run_export_cmd(args: &mut impl Iterator<Item = String>) {
    let mut output = PathBuf::from("/app/output/settlement-report.json");
    while let Some(flag) = args.next() {
        match flag.as_str() {
            "--output" => output = PathBuf::from(args.next().expect("--output value")),
            _ => usage(),
        }
    }
    let report = run_export(&output).unwrap_or_else(|e| {
        eprintln!("export failed: {e}");
        process::exit(1);
    });
    write_report(&output, &report).unwrap_or_else(|e| {
        eprintln!("write failed: {e}");
        process::exit(1);
    });
}

fn run_replay_cmd(args: &mut impl Iterator<Item = String>) {
    let opts = parse_replay_flags(args);
    run_replay(&opts.season, &opts.events, &opts.seasons_dir, &opts.output).unwrap_or_else(|e| {
        eprintln!("replay failed: {e}");
        process::exit(1);
    });
}

struct ReplayOpts {
    season: PathBuf,
    events: PathBuf,
    seasons_dir: PathBuf,
    output: PathBuf,
}

fn parse_replay_flags(args: &mut impl Iterator<Item = String>) -> ReplayOpts {
    let mut season = PathBuf::from("/app/fixtures/seasons/winter-alpha.json");
    let mut events = PathBuf::from("/app/fixtures/events/alpha-stream.jsonl");
    let mut seasons_dir = PathBuf::from("/app/fixtures/seasons");
    let mut output = PathBuf::from("/app/output/settlement-report.json");

    while let Some(flag) = args.next() {
        match flag.as_str() {
            "--season" => season = PathBuf::from(args.next().expect("--season value")),
            "--events" => events = PathBuf::from(args.next().expect("--events value")),
            "--seasons-dir" => seasons_dir = PathBuf::from(args.next().expect("--seasons-dir value")),
            "--output" => output = PathBuf::from(args.next().expect("--output value")),
            _ => usage(),
        }
    }

    ReplayOpts {
        season,
        events,
        seasons_dir,
        output,
    }
}

fn usage() -> ! {
    eprintln!(
        "usage:\n  lootsettle ingest --season PATH --events PATH\n  lootsettle settle --seasons-dir PATH\n  lootsettle export --output PATH\n  lootsettle replay --season PATH --events PATH --seasons-dir PATH --output PATH"
    );
    process::exit(2);
}
