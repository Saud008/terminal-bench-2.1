use clap::{Parser, Subcommand};
use irrctl_engine::pack_loader;
use irrctl_engine::m08_ledger;
use irrctl_engine::m09_publish;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "veldt-cli")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    LoadPack { #[arg(long)] orchard: String, #[arg(long)] run_id: String },
    BuildLedger { #[arg(long)] run_id: String },
    PublishPlan { #[arg(long)] run_id: String, #[arg(long)] output: PathBuf },
}

fn orchard_root() -> PathBuf {
    std::env::var("ORCHARD_SCENARIO_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/app/fixtures/orchards"))
}

fn ledger_path() -> PathBuf {
    PathBuf::from("/app/state/moisture-ledger.json")
}

fn pack_meta_path(run_id: &str) -> PathBuf {
    PathBuf::from(format!("/app/work/pack-{run_id}.json"))
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::LoadPack { orchard, run_id } => {
            let path = orchard_root().join(&orchard).join("orchard.json");
            let meta = pack_loader::load_orchard(&path).expect("load-pack");
            fs::write(pack_meta_path(&run_id), serde_json::to_string_pretty(&meta).unwrap()).unwrap();
        }
        Cmd::BuildLedger { run_id } => {
            let raw = fs::read_to_string(pack_meta_path(&run_id)).expect("build-ledger pack");
            let meta: irrctl_engine::field_schema::OrchardMeta = serde_json::from_str(&raw).unwrap();
            let ledger = m08_ledger::build_moisture_ledger(&run_id, &meta);
            fs::write(ledger_path(), serde_json::to_string_pretty(&ledger).unwrap()).unwrap();
        }
        Cmd::PublishPlan { run_id, output } => {
            let raw = fs::read_to_string(ledger_path()).expect("publish ledger");
            let ledger: irrctl_engine::field_schema::MoistureLedger = serde_json::from_str(&raw).unwrap();
            assert_eq!(ledger.run_id, run_id);
            let pack_raw = fs::read_to_string(pack_meta_path(&run_id)).expect("publish pack");
            let meta: irrctl_engine::field_schema::OrchardMeta = serde_json::from_str(&pack_raw).unwrap();
            let plan = m09_publish::publish_plan(&ledger, &meta.fields);
            fs::write(output, serde_json::to_string_pretty(&plan).unwrap()).unwrap();
        }
    }
}
