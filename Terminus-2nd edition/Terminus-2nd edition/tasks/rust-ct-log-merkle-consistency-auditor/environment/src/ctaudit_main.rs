use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "ctwrelease")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Stage {
        #[arg(long)]
        audit_index: PathBuf,
        #[arg(long)]
        witness_ledger: PathBuf,
        #[arg(long)]
        staging: PathBuf,
    },
    Seal {
        #[arg(long)]
        staging: PathBuf,
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let result = match cli.command {
        Commands::Stage {
            audit_index,
            witness_ledger,
            staging,
        } => ctaudit::exportkit::snapshot_lines::materialize_checkpoint_rows(&audit_index, &witness_ledger, &staging),
        Commands::Seal { staging, out } => ctaudit::exportkit::capsule_emit::write_sealed_archive(&staging, &out),
    };
    if let Err(e) = result {
        eprintln!("ctwrelease error: {e}");
        std::process::exit(1);
    }
}
