use std::path::PathBuf;

use clap::{Parser, Subcommand};
use fitcore::export_laps;
use fitcore::parse::parse_file;

#[derive(Parser)]
#[command(name = "fitlap")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Decode {
        fit_file: PathBuf,
    },
    Laps {
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
        Commands::Decode { fit_file } => match run_decode(&fit_file) {
            Ok(()) => 0,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
        Commands::Laps {
            export,
            input,
            stem,
            output,
        } => match run_laps(export, &input, &stem, &output) {
            Ok(()) => 0,
            Err(err) => {
                eprintln!("{err}");
                1
            }
        },
    };
    std::process::exit(code);
}

fn run_decode(path: &PathBuf) -> Result<(), fitcore::FitError> {
    let laps = parse_file(path, true)?;
    let summary = serde_json::json!({
        "source": path.display().to_string(),
        "lap_count": laps.len(),
    });
    println!(
        "{}",
        serde_json::to_string_pretty(&summary).map_err(|e| fitcore::FitError::Parse(e.to_string()))?
    );
    Ok(())
}

fn run_laps(
    export: bool,
    input: &PathBuf,
    stem: &str,
    output: &PathBuf,
) -> Result<(), fitcore::FitError> {
    if !export {
        return Err(fitcore::FitError::Parse(
            "laps requires --export for this task".to_string(),
        ));
    }
    let report = export_laps(input, stem)?;
    if let Some(parent) = output.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(output, serde_json::to_string_pretty(&report)?)?;
    Ok(())
}
