use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};
use slcore::export_catalog;
use slcore::ingest::ingest_snippet;
use slcore::parse::parse_file;

#[derive(Parser)]
#[command(name = "seedcat")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Decode {
        slws_file: PathBuf,
    },
    Ingest {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        stem: String,
    },
    Catalog {
        #[arg(long)]
        export: bool,
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        stem: String,
        #[arg(long)]
        output: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Decode { slws_file } => match run_decode(&slws_file) {
            Ok(()) => 0,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
        Commands::Ingest { input, stem } => match run_ingest(&input, &stem) {
            Ok(()) => 0,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
        Commands::Catalog {
            export,
            input,
            stem,
            output,
        } => match run_catalog(export, &input, &stem, &output) {
            Ok(()) => 0,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
    };
    std::process::exit(code);
}

fn run_decode(path: &PathBuf) -> Result<(), slcore::SlError> {
    let msg = parse_file(path, true)?;
    let summary = serde_json::json!({
        "source": path.display().to_string(),
        "pick_count": msg.picks.len(),
        "sample_count": msg.sample_count,
    });
    println!(
        "{}",
        serde_json::to_string_pretty(&summary)
            .map_err(|e| slcore::SlError::Parse(e.to_string()))?
    );
    Ok(())
}

fn run_ingest(input: &PathBuf, stem: &str) -> Result<(), slcore::SlError> {
    ingest_snippet(input, stem)?;
    Ok(())
}

fn run_catalog(
    export: bool,
    input: &PathBuf,
    stem: &str,
    output: &PathBuf,
) -> Result<(), slcore::SlError> {
    if !export {
        return Err(slcore::SlError::Parse(
            "catalog requires --export for this task".to_string(),
        ));
    }
    let report = export_catalog(input, stem)?;
    if let Some(parent) = output.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(output, serde_json::to_string_pretty(&report)?)?;
    Ok(())
}
