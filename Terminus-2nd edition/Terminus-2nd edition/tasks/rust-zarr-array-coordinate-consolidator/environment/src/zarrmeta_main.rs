use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "zarrmeta")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Ingest {
        #[arg(long)]
        manifest_dir: PathBuf,
        #[arg(long)]
        axes: PathBuf,
        #[arg(long)]
        staging: PathBuf,
    },
    Export {
        #[arg(long)]
        staging: PathBuf,
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let result = match cli.command {
        Commands::Ingest {
            manifest_dir,
            axes,
            staging,
        } => zarrmeta::row_stage::build_staging_snapshot(&manifest_dir, &axes, &staging),
        Commands::Export { staging, out } => zarrmeta::manifest_writer::write_consolidated_manifest(&staging, &out),
    };
    if let Err(e) = result {
        eprintln!("zarrmeta error: {e}");
        std::process::exit(1);
    }
}
