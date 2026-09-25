use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "wbleguard")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    #[command(name = "catalog-bundles")]
    CatalogBundles {
        #[arg(long)]
        bundles_dir: PathBuf,
        #[arg(long)]
        staging: PathBuf,
    },
    #[command(name = "emit-attestation")]
    EmitAttestation {
        #[arg(long)]
        staging: PathBuf,
        #[arg(long, default_value = "/app/environment/fixtures/bundle_meta.json")]
        meta: PathBuf,
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let res = match cli.cmd {
        Commands::CatalogBundles { bundles_dir, staging } => {
            wbleguard::attestation_ledger::ingest_bundles(&bundles_dir, &staging)
        }
        Commands::EmitAttestation { staging, meta, out } => {
            wbleguard::attestation_emit::export_evidence(&staging, &meta, &out)
        }
    };
    if let Err(e) = res {
        eprintln!("wbleguard error: {e}");
        std::process::exit(1);
    }
}
