use std::fs;
use std::path::PathBuf;

use clap::Parser;
use combat_core::{export_transcript, ingest_roster, read_state, simulate_combat, write_state, CombatError};

#[derive(Parser)]
#[command(name = "turnctl")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(clap::Subcommand)]
enum Commands {
    Ingest {
        #[arg(long)]
        roster: PathBuf,
        #[arg(long)]
        staging: PathBuf,
    },
    Simulate {
        #[arg(long)]
        staging: PathBuf,
        #[arg(long)]
        seed: String,
        #[arg(long)]
        state: PathBuf,
        #[arg(long)]
        export: PathBuf,
    },
    Export {
        #[arg(long)]
        state: PathBuf,
        #[arg(long)]
        export: PathBuf,
    },
}

fn write_json<T: serde::Serialize>(path: &PathBuf, doc: &T) -> Result<(), CombatError> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let json = serde_json::to_string_pretty(doc).map_err(CombatError::Json)?;
    fs::write(path, format!("{json}\n"))?;
    Ok(())
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Ingest { roster, staging } => match ingest_roster(&roster, &staging) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
        Commands::Simulate {
            staging,
            seed,
            state,
            export,
        } => run_simulate(&staging, &seed, &state, &export),
        Commands::Export { state, export } => run_export(&state, &export),
    };
    std::process::exit(code);
}

fn run_simulate(staging: &PathBuf, seed: &str, state_path: &PathBuf, export_path: &PathBuf) -> i32 {
    let raw = match fs::read_to_string(staging) {
        Ok(v) => v,
        Err(err) => {
            eprintln!("{err}");
            return 1;
        }
    };
    let staging_doc: combat_core::model::StagingDoc = match serde_json::from_str(&raw) {
        Ok(v) => v,
        Err(err) => {
            eprintln!("{err}");
            return 1;
        }
    };
    let state = simulate_combat(&staging_doc, seed);
    if write_state(state_path, &state).is_err() {
        return 1;
    }
    let transcript = export_transcript(&state);
    write_json(export_path, &transcript).map(|_| 0).unwrap_or(1)
}

fn run_export(state_path: &PathBuf, export_path: &PathBuf) -> i32 {
    let state = match read_state(state_path) {
        Ok(v) => v,
        Err(err) => {
            eprintln!("{err}");
            return 1;
        }
    };
    let transcript = export_transcript(&state);
    write_json(export_path, &transcript).map(|_| 0).unwrap_or(1)
}
