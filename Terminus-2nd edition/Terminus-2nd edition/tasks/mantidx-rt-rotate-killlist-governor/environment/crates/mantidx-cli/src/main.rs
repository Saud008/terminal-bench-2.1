use clap::{Parser, Subcommand};
use mantidx_core::{
    index_batch, queue_delete, run_merge_ram, run_rotate, run_search, run_update_attr,
};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "mantidx", about = "Manticore-style RT index rotate lab")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Insert {
        #[arg(long)]
        batch: PathBuf,
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/mantidx.db")]
        db: PathBuf,
    },
    Delete {
        #[arg(long)]
        query: String,
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/mantidx.db")]
        db: PathBuf,
    },
    Rotate {
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/mantidx.db")]
        db: PathBuf,
    },
    MergeRam {
        #[arg(long)]
        left: String,
        #[arg(long)]
        right: String,
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/mantidx.db")]
        db: PathBuf,
    },
    UpdateAttr {
        #[arg(long)]
        doc_id: i64,
        #[arg(long)]
        price: i64,
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/mantidx.db")]
        db: PathBuf,
    },
    Search {
        #[arg(long)]
        query: String,
        #[arg(long, default_value = "/app/state")]
        state: PathBuf,
        #[arg(long, default_value = "/app/data/mantidx.db")]
        db: PathBuf,
        #[arg(long, default_value = "/app/state/search-report.json")]
        report: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    let code = match cli.command {
        Commands::Insert { batch, state, db } => match index_batch(&db, &batch, &state) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("insert failed: {err}");
                1
            }
        },
        Commands::Delete { query, state, db } => match queue_delete(&state, &db, &query) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("delete failed: {err}");
                1
            }
        },
        Commands::Rotate { state, db } => match run_rotate(&state, &db) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("rotate failed: {err}");
                1
            }
        },
        Commands::MergeRam {
            left,
            right,
            state,
            db,
        } => match run_merge_ram(&state, &db, &left, &right) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("merge-ram failed: {err}");
                1
            }
        },
        Commands::UpdateAttr {
            doc_id,
            price,
            state,
            db,
        } => match run_update_attr(&state, &db, doc_id, price) {
            Ok(_) => 0,
            Err(err) => {
                eprintln!("update-attr failed: {err}");
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
