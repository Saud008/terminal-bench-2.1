use crate::s5pipe::ledger;
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(name = "s5lineage", version, about = "S5 dataset chunk lineage profiler")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    Ingest {
        #[arg(long)]
        catalog: PathBuf,
        #[arg(long)]
        state: PathBuf,
    },
    Export {
        #[arg(long)]
        state: PathBuf,
        #[arg(long)]
        out: PathBuf,
    },
}

impl Cli {
    pub fn run() -> Result<(), String> {
        let hdclp_cli = Cli::parse();
        match hdclp_cli.command {
            Commands::Ingest { catalog, state } => ledger::run_ingest(&catalog, &state),
            Commands::Export { state, out } => crate::s5pipe::emit::run_export(&state, &out),
        }
    }
}
