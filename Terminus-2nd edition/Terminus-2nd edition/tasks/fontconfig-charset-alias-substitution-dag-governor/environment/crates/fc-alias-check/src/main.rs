use std::path::PathBuf;

use clap::{Parser, Subcommand};
use fc_alias_core::dag::find_cycle;
use fc_alias_core::ingest::load_merged;
use fc_alias_core::export::resolve_request;
use fc_alias_core::staging::{build_stage, load_stage, save_stage, stage_path_from_env};
use fc_alias_core::{FcError, Result};

#[derive(Parser)]
#[command(name = "fc-alias-check")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Ingest {
        #[arg(long)]
        config: PathBuf,
        #[arg(long)]
        inject: Option<PathBuf>,
    },
    Resolve {
        #[arg(long)]
        charset: String,
        #[arg(long)]
        family: String,
        #[arg(long)]
        export: PathBuf,
    },
    Check {
        #[arg(long)]
        config: PathBuf,
        #[arg(long)]
        inject: Option<PathBuf>,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Ingest { config, inject } => match run_ingest(&config, inject.as_ref()) {
            Ok(()) => 0,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
        Commands::Resolve {
            charset,
            family,
            export,
        } => match run_resolve(&charset, &family, &export) {
            Ok(()) => 0,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
        Commands::Check { config, inject } => match run_check(&config, inject.as_ref()) {
            Ok(()) => 0,
            Err(FcError::CycleDetected) => {
                eprintln!("alias cycle detected");
                2
            }
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
    };
    std::process::exit(code);
}

fn run_ingest(config: &PathBuf, inject: Option<&PathBuf>) -> Result<()> {
    let cfg = load_merged(config, inject.map(|p| p.as_path()))?;
    let stage = build_stage(cfg, config, inject.map(|p| p.as_path()))?;
    save_stage(&stage_path_from_env().display().to_string(), &stage)?;
    Ok(())
}

fn run_resolve(charset: &str, family: &str, export: &PathBuf) -> Result<()> {
    let stage_path = stage_path_from_env();
    if !stage_path.is_file() {
        return Err(FcError::StagingMissing);
    }
    let stage = load_stage(&stage_path.display().to_string())?;
    find_cycle(&stage.config)?;
    let doc = resolve_request(&stage.config, charset, family, &stage.compile_meta)?;
    let json = serde_json::to_string_pretty(&doc).map_err(|e| FcError::Io(e.to_string()))?;
    std::fs::write(export, json).map_err(|e| FcError::Io(e.to_string()))?;
    Ok(())
}

fn run_check(config: &PathBuf, inject: Option<&PathBuf>) -> Result<()> {
    let cfg = load_merged(config, inject.map(|p| p.as_path()))?;
    find_cycle(&cfg)
}
