use clap::{Parser, Subcommand};
use shift_pl_engine::mw10;
use shift_pl_engine::mw07;
use shift_pl_engine::mw08;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "shift-pl")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Latch { #[arg(long)] scenario: String, #[arg(long)] run_id: String },
    Curate { #[arg(long)] run_id: String },
    Publish { #[arg(long)] run_id: String, #[arg(long)] output: PathBuf },
}

fn scenario_root() -> PathBuf {
    std::env::var("SHIFT_SCENARIO_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/app/fixtures/scenarios"))
}

fn harmonized_path() -> PathBuf {
    PathBuf::from("/app/state/shift-harmonized.json")
}

fn latch_meta_path(run_id: &str) -> PathBuf {
    PathBuf::from(format!("/app/work/latch-{run_id}.json"))
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Latch { scenario, run_id } => {
            let path = scenario_root().join(&scenario).join("scenario.json");
            let meta = mw10::latch_scenario(&path).expect("latch");
            fs::write(latch_meta_path(&run_id), serde_json::to_string_pretty(&meta).unwrap()).unwrap();
        }
        Cmd::Curate { run_id } => {
            let raw = fs::read_to_string(latch_meta_path(&run_id)).expect("curate latch");
            let meta: shift_pl_engine::mw11::ScenarioMeta = serde_json::from_str(&raw).unwrap();
            let ledger = mw07::curate_run(&run_id, &meta);
            fs::write(harmonized_path(), serde_json::to_string_pretty(&ledger).unwrap()).unwrap();
        }
        Cmd::Publish { run_id, output } => {
            let raw = fs::read_to_string(harmonized_path()).expect("publish harmonized");
            let ledger: shift_pl_engine::mw11::HarmonizedLedger = serde_json::from_str(&raw).unwrap();
            assert_eq!(ledger.run_id, run_id);
            let atlas = mw08::publish_atlas(&ledger);
            fs::write(output, serde_json::to_string_pretty(&atlas).unwrap()).unwrap();
        }
    }
}
