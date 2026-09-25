use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand};

use geojson_core::run_repair;

#[derive(Parser)]
#[command(name = "geojson-fix")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Repair {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        output: PathBuf,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Repair { input, output } => {
            run_repair(&input, &output)?;
        }
    }
    Ok(())
}
