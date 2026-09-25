use clap::{Parser, Subcommand};
use navmesh_core::{run_path, run_validate};
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "navmeshctl")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Validate {
        #[arg(long)]
        mesh: PathBuf,
        #[arg(long)]
        seed: u64,
        #[arg(long)]
        export: PathBuf,
    },
    Path {
        #[arg(long)]
        mesh: PathBuf,
        #[arg(long)]
        seed: u64,
        #[arg(long)]
        from: String,
        #[arg(long)]
        to: String,
        #[arg(long)]
        export: PathBuf,
    },
}

fn write_json(path: &PathBuf, value: &impl serde::Serialize) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let raw = serde_json::to_string_pretty(value).map_err(|e| e.to_string())?;
    fs::write(path, raw + "\n").map_err(|e| e.to_string())
}

fn main() {
    let cli = Cli::parse();
    let result = match cli.command {
        Commands::Validate { mesh, seed, export } => run_validate(&mesh, seed).and_then(|v| {
            write_json(&export, &v)?;
            Ok(())
        }),
        Commands::Path {
            mesh,
            seed,
            from,
            to,
            export,
        } => run_path(&mesh, seed, &from, &to).and_then(|p| {
            write_json(&export, &p)?;
            Ok(())
        }),
    };

    if let Err(err) = result {
        eprintln!("{err}");
        std::process::exit(1);
    }
}
