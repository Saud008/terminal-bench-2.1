use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand};

use bag_audit::pipeline;

#[derive(Parser)]
#[command(name = "bag-audit")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Audit {
        #[arg(long)]
        bag: PathBuf,
        #[arg(long, default_value = "1.0")]
        speed: f64,
        #[arg(long, default_value = "0")]
        seed: u64,
        #[arg(long)]
        export: PathBuf,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Audit {
            bag,
            speed,
            seed,
            export,
        } => pipeline::run_audit(&bag, &export, speed, seed),
    }
}
