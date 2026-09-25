use clap::{Parser, Subcommand};
use k7cal_engine::m02_bind;
use k7cal_engine::m04_journal;
use k7cal_engine::m07_emit;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "k7cal")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Bind { #[arg(long)] scenario: String, #[arg(long)] run_id: String },
    Weave { #[arg(long)] run_id: String },
    Seal { #[arg(long)] run_id: String, #[arg(long)] output: PathBuf },
}

fn scenario_root() -> PathBuf {
    if let Ok(tb3) = std::env::var("TB3_FIXTURE_DIR") {
        return PathBuf::from(tb3);
    }
    std::env::var("EVAC_SCENARIO_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/app/fixtures/scenarios"))
}

fn bind_path(run_id: &str) -> PathBuf {
    PathBuf::from(format!("/app/work/bind-{run_id}.json"))
}

fn ledger_path() -> PathBuf {
    PathBuf::from("/app/state/evac-lane-ledger.json")
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Bind { scenario, run_id } => {
            let bundle = m02_bind::bind_scenario(&scenario_root(), &scenario).expect("bind");
            fs::write(bind_path(&run_id), serde_json::to_string_pretty(&bundle).unwrap()).unwrap();
        }
        Cmd::Weave { run_id } => {
            let raw = fs::read_to_string(bind_path(&run_id)).expect("weave bind");
            let bundle: k7cal_engine::hazard_schema::BindBundle = serde_json::from_str(&raw).unwrap();
            let ledger = m04_journal::weave_run(&run_id, &bundle);
            fs::write(ledger_path(), serde_json::to_string_pretty(&ledger).unwrap()).unwrap();
        }
        Cmd::Seal { run_id, output } => {
            let raw = fs::read_to_string(ledger_path()).expect("seal ledger");
            let ledger: k7cal_engine::hazard_schema::WeaveLedger = serde_json::from_str(&raw).unwrap();
            assert_eq!(ledger.run_id, run_id);
            let sealed = m07_emit::seal_bundle(&ledger);
            fs::write(output, serde_json::to_string_pretty(&sealed).unwrap()).unwrap();
        }
    }
}
