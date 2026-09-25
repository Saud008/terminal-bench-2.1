mod app;
mod batch;
mod collator;
mod decoy;
mod errors;
mod export;
mod id;
mod merge;
mod model;
mod segment;
mod state;

use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "blevectl")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Ingest {
        #[arg(long)]
        index: String,
        #[arg(long)]
        batch: PathBuf,
    },
    Export {
        #[arg(long)]
        index: String,
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    if let Err(err) = run() {
        eprintln!("{err}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), errors::BleveError> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Ingest { index, batch } => app::run_ingest(&index, &batch),
        Commands::Export { index, out } => app::run_export(&index, &out),
    }
}
