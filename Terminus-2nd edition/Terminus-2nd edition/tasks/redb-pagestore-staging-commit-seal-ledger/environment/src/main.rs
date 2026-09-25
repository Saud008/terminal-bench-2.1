use redbtool::commit::commit_table;
use redbtool::export::export_table;
use redbtool::ingest::apply_batch_file;
use redbtool::staging::delete_key;
use redbtool::walk::walk_table;
use std::path::PathBuf;

use clap::Parser;

#[derive(Debug, Parser)]
#[command(name = "redbtool")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Parser)]
enum Command {
    /// Apply JSONL put/delete ops to the staging table.
    Batch {
        #[arg(long)]
        table: String,
        #[arg(long)]
        input: PathBuf,
    },
    /// Delete a single key from staging.
    Delete {
        #[arg(long)]
        table: String,
        #[arg(long)]
        key: String,
    },
    /// Commit staging into committed storage and write btree-snapshot.json.
    Commit {
        #[arg(long)]
        table: String,
    },
    /// Export committed table keys as sorted JSON array.
    Export {
        #[arg(long)]
        table: String,
        #[arg(long)]
        out: PathBuf,
    },
    /// Report leaf count and root height for committed table.
    Walk {
        #[arg(long)]
        table: String,
    },
}

fn resolve_table(table: &str) -> String {
    if let Ok(prefix) = std::env::var("TB3_TABLE_PREFIX") {
        if prefix.starts_with('/') {
            return format!("{}/{}", prefix.trim_end_matches('/'), table);
        }
    }
    table.to_string()
}

fn main() -> Result<(), String> {
    let cli = Cli::parse();
    match cli.command {
        Command::Batch { table, input } => {
            let name = resolve_table(&table);
            apply_batch_file(&name, &input)
        }
        Command::Delete { table, key } => {
            let name = resolve_table(&table);
            delete_key(&name, &key)
        }
        Command::Commit { table } => {
            let name = resolve_table(&table);
            commit_table(&name)
        }
        Command::Export { table, out } => {
            let name = resolve_table(&table);
            export_table(&name, &out)
        }
        Command::Walk { table } => {
            let name = resolve_table(&table);
            let report = walk_table(&name)?;
            println!("{}", serde_json::to_string(&report).map_err(|e| e.to_string())?);
            Ok(())
        }
    }
}
