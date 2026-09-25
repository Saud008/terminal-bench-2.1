use clap::{Parser, Subcommand};
use std::path::PathBuf;
use xr7_engine::wx_finalize_report;
use xr7_engine::wx_roll_journal;

#[derive(Parser)]
#[command(name = "xr7")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    CatalogScan {
        #[arg(long = "catalog-dir")]
        catalog_dir: PathBuf,
        #[arg(long = "weight-root")]
        weight_root: PathBuf,
        #[arg(long)]
        journal: PathBuf,
    },
    AtlasPublish {
        #[arg(long)]
        journal: PathBuf,
        #[arg(long = "catalog-dir")]
        catalog_dir: PathBuf,
        #[arg(long = "weight-root")]
        weight_root: PathBuf,
        #[arg(long)]
        atlas: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.cmd {
        Cmd::CatalogScan {
            catalog_dir,
            weight_root,
            journal,
        } => match wx_roll_journal::wx_roll_journal(&catalog_dir, &weight_root, &journal) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("catalog-scan error: {e}");
                1
            }
        },
        Cmd::AtlasPublish {
            journal,
            catalog_dir,
            weight_root,
            atlas,
        } => match wx_finalize_report::wx_finalize_report(&journal, &catalog_dir, &weight_root, &atlas) {
            Ok(()) => 0,
            Err(e) => {
                eprintln!("atlas-publish error: {e}");
                1
            }
        },
    };
    std::process::exit(code);
}
