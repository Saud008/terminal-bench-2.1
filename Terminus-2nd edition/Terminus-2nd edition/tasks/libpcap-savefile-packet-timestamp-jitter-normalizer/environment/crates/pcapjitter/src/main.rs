use std::path::PathBuf;

use clap::{Parser, Subcommand};

use pcapjitter::{run_export, run_ingest};

#[derive(Parser)]
#[command(name = "pcapjitter")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Ingest {
        #[arg(long)]
        input: String,
        #[arg(long)]
        staging: PathBuf,
        #[arg(long)]
        ledger_root: PathBuf,
    },
    Export {
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        staging: PathBuf,
        #[arg(long)]
        ledger_root: PathBuf,
    },
}

fn main() {
    let code = match Cli::parse().command {
        Commands::Ingest {
            input,
            staging,
            ledger_root,
        } => match run_ingest(
            &input,
            staging.to_str().unwrap_or(""),
            ledger_root.to_str().unwrap_or(""),
        ) {
            Ok(c) => c,
            Err(e) => {
                eprintln!("{e}");
                2
            }
        },
        Commands::Export {
            output,
            staging,
            ledger_root,
        } => match run_export(
            staging.to_str().unwrap_or(""),
            output.to_str().unwrap_or(""),
            ledger_root.to_str().unwrap_or(""),
        ) {
            Ok(c) => c,
            Err(e) => {
                eprintln!("{e}");
                2
            }
        },
    };
    std::process::exit(code);
}
