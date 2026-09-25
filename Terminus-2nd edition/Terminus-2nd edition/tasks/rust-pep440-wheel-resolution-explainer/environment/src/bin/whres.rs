use clap::{Parser, Subcommand};
use std::path::PathBuf;
use whres_engine::analyze_run;
use whres_engine::m07;
use whres_engine::m08;
use whres_engine::m06::SnapshotDoc;

#[derive(Parser)]
#[command(name = "whres")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Load {
        #[arg(long)]
        scenario: String,
        #[arg(long = "run-id")]
        run_id: String,
    },
    Analyze {
        #[arg(long = "run-id")]
        run_id: String,
    },
    Emit {
        #[arg(long = "run-id")]
        run_id: String,
        #[arg(long)]
        output: PathBuf,
    },
}

fn scenario_root() -> PathBuf {
    if let Ok(v) = std::env::var("WHRES_SCENARIO_ROOT") {
        return PathBuf::from(v);
    }
    PathBuf::from("/app/fixtures/scenarios")
}

fn main() {
    let cli = Cli::parse();
    let work = PathBuf::from("/app/work");
    let state = PathBuf::from("/app/state");
    std::fs::create_dir_all(&work).ok();
    std::fs::create_dir_all(&state).ok();
    let code = match cli.cmd {
        Cmd::Load { scenario, run_id } => {
            match m08::bundle_load(&scenario_root(), &scenario, &run_id, &work) {
                Ok(()) => 0,
                Err(e) => {
                    eprintln!("load error: {e}");
                    1
                }
            }
        }
        Cmd::Analyze { run_id } => match analyze_run::analyze_run(&work, &state, &run_id) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("analyze error: {e}");
                1
            }
        },
        Cmd::Emit { run_id, output } => {
            let snap_path = state.join("whres-snapshot.json");
            let raw = match std::fs::read_to_string(&snap_path) {
                Ok(s) => s,
                Err(e) => {
                    eprintln!("emit read snapshot: {e}");
                    return;
                }
            };
            let snap_doc: SnapshotDoc = match serde_json::from_str(&raw) {
                Ok(s) => s,
                Err(e) => {
                    eprintln!("emit parse snapshot: {e}");
                    return;
                }
            };
            if snap_doc.run_id != run_id {
                eprintln!("run_id mismatch");
                return;
            }
            match m07::emit_report(&snap_doc, &output) {
                Ok(()) => 0,
                Err(e) => {
                    eprintln!("emit error: {e}");
                    1
                }
            }
        }
    };
    std::process::exit(code);
}
