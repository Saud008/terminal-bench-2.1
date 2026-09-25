use std::path::PathBuf;

use clap::Parser;

#[derive(Parser)]
#[command(name = "ldif-apply")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(clap::Subcommand)]
enum Commands {
    Apply {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        seed: String,
        #[arg(long)]
        export: PathBuf,
        #[arg(long)]
        audit_db: PathBuf,
    },
    AuditQuery {
        #[arg(long)]
        audit_db: PathBuf,
        #[arg(long)]
        seed: String,
        #[arg(long)]
        export: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Apply {
            input,
            seed,
            export,
            audit_db,
        } => match ldif_core::apply_file(&input, &seed, &export, &audit_db) {
            Ok(()) => 0,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
        Commands::AuditQuery {
            audit_db,
            seed,
            export,
        } => match ldif_core::query_audit(&audit_db, &seed, &export) {
            Ok(code) => code,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
    };
    std::process::exit(code);
}
