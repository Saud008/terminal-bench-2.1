            use clap::{Parser, Subcommand};
            use ingest_stage::store::ingest_batch;
            use search_export::score_stage::run_query;
            use std::path::PathBuf;
            use xapi_types::index::IndexFile;

            #[derive(Parser)]
            #[command(name = "xapian-weight-cli")]
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
                Query {
                    #[arg(long)]
                    index: PathBuf,
                    #[arg(long)]
                    query: String,
                    #[arg(long)]
                    output: PathBuf,
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
                    Commands::Query {
                        index,
                        query,
                        output,
                    } => {
                        let file = IndexFile::load(&index)?;
                        let result = run_query(&file, &query)?;
                        let data = serde_json::to_string_pretty(&result).map_err(|e| e.to_string())?;
                        std::fs::write(&output, format!("{data}
")).map_err(|e| e.to_string())?;
                    }
                }
                Ok(())
            }
