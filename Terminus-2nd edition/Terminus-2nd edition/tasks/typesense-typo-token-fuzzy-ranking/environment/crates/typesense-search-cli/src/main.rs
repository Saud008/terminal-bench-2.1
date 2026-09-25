use clap::{Parser, Subcommand};
use ingest_stage::store::ingest_batch;
use search_export::search_stage::run_search;
use std::path::PathBuf;
use ts_types::index::IndexFile;

#[derive(Parser)]
#[command(name = "typesense-search-cli")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Index {
        #[arg(long)]
        index: PathBuf,
        #[arg(long)]
        batch: PathBuf,
    },
    Search {
        #[arg(long)]
        index: PathBuf,
        #[arg(long)]
        query: String,
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        filter_brand: Option<String>,
    },
}

fn main() {
    if let Err(err) = run() {
        eprintln!("{err}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Index { index, batch } => {
            ingest_batch(&index, &batch)?;
        }
        Commands::Search {
            index,
            query,
            output,
            filter_brand,
        } => {
            let file = IndexFile::load(&index)?;
            let result = run_search(&file, &query, filter_brand.as_deref())?;
            let data = serde_json::to_string_pretty(&result).map_err(|e| e.to_string())?;
            std::fs::write(&output, format!("{data}\n")).map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}
