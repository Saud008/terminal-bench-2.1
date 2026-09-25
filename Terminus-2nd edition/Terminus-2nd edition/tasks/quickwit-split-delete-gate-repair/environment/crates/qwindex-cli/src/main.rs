use clap::{Parser, Subcommand};
use qwindex_core::{index_batch, publish_split, run_delete, run_merge, run_search};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "qwindex", about = "Split/merge index repair lab")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Index {
        #[arg(long)]
        batch: PathBuf,
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/qwindex.db")]
        db: PathBuf,
    },
    SplitPublish {
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/qwindex.db")]
        db: PathBuf,
    },
    Delete {
        #[arg(long)]
        query: String,
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/qwindex.db")]
        db: PathBuf,
    },
    Merge {
        #[arg(long)]
        left: String,
        #[arg(long)]
        right: String,
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/qwindex.db")]
        db: PathBuf,
    },
    Search {
        #[arg(long)]
        query: String,
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/qwindex.db")]
        db: PathBuf,
        #[arg(long, default_value = "/app/state/search-report.json")]
        report: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Index { batch, state: _, db } => match index_batch(&db, &batch) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("index failed: {err}");
                1
            }
        },
        Commands::SplitPublish { state, db } => match publish_split(&state, &db) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("split publish failed: {err}");
                1
            }
        },
        Commands::Delete { query, state, db } => match run_delete(&state, &db, &query) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("delete failed: {err}");
                1
            }
        },
        Commands::Merge {
            left,
            right,
            state,
            db,
        } => match run_merge(&state, &db, &left, &right) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("merge failed: {err}");
                1
            }
        },
        Commands::Search {
            query,
            state,
            db,
            report,
        } => match run_search(&state, &db, &query, &report) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("search failed: {err}");
                1
            }
        },
    };
    std::process::exit(code);
}
