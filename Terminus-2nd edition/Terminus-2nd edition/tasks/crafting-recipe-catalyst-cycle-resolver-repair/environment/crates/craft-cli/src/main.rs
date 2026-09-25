use clap::{Parser, Subcommand};
use craft_core::detect_cycles;
use inventory_db::dao::load_recipe_book;
use inventory_db::{open_db, InventoryDao};
use serde_json;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "crafter")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Seed {
        #[arg(long)]
        seed: String,
        #[arg(long)]
        profile: PathBuf,
        #[arg(long)]
        db: PathBuf,
    },
    Preview {
        #[arg(long)]
        seed: String,
        #[arg(long)]
        recipe: String,
        #[arg(long)]
        qty: u32,
        #[arg(long)]
        recipes: PathBuf,
        #[arg(long)]
        db: PathBuf,
    },
    Apply {
        #[arg(long)]
        seed: String,
        #[arg(long)]
        recipe: String,
        #[arg(long)]
        qty: u32,
        #[arg(long)]
        recipes: PathBuf,
        #[arg(long)]
        db: PathBuf,
    },
    ValidateGraph {
        #[arg(long)]
        recipes: PathBuf,
    },
    Export {
        #[arg(long)]
        db: PathBuf,
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();
    if let Err(err) = run(cli) {
        eprintln!("{err}");
        std::process::exit(1);
    }
}

fn run(cli: Cli) -> Result<(), String> {
    match cli.command {
        Commands::Seed { seed: _, profile, db } => {
            let raw = std::fs::read_to_string(&profile).map_err(|e| e.to_string())?;
            let profile_data: serde_json::Value =
                serde_json::from_str(&raw).map_err(|e| e.to_string())?;
            let slots: Vec<craft_core::model::InventorySlot> =
                serde_json::from_value(profile_data["slots"].clone())
                    .map_err(|e| e.to_string())?;
            let slot_limit = profile_data["slot_limit"]
                .as_u64()
                .ok_or_else(|| "profile missing slot_limit".to_string())? as u32;
            let conn = open_db(db.to_str().ok_or("bad db path")?).map_err(|e| e.to_string())?;
            InventoryDao::new(&conn).seed_profile(&slots, slot_limit)?;
            println!("seeded");
            Ok(())
        }
        Commands::Preview {
            seed: _,
            recipe,
            qty,
            recipes,
            db,
        } => {
            let book = load_recipe_book(&recipes)?;
            let conn = open_db(db.to_str().ok_or("bad db path")?).map_err(|e| e.to_string())?;
            let dao = InventoryDao::new(&conn);
            let preview = dao.preview(&book, &recipe, qty)?;
            let json = serde_json::to_string_pretty(&preview).map_err(|e| e.to_string())?;
            println!("{json}");
            if !preview.ok {
                std::process::exit(2);
            }
            Ok(())
        }
        Commands::Apply {
            seed: _,
            recipe,
            qty,
            recipes,
            db,
        } => {
            let book = load_recipe_book(&recipes)?;
            let conn = open_db(db.to_str().ok_or("bad db path")?).map_err(|e| e.to_string())?;
            let dao = InventoryDao::new(&conn);
            let result = dao.apply(&book, &recipe, qty)?;
            let json = serde_json::to_string_pretty(&result).map_err(|e| e.to_string())?;
            println!("{json}");
            Ok(())
        }
        Commands::ValidateGraph { recipes } => {
            let book = load_recipe_book(&recipes)?;
            let report = detect_cycles(&book);
            let json = serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?;
            println!("{json}");
            if report.cyclic {
                std::process::exit(3);
            }
            Ok(())
        }
        Commands::Export { db, out } => {
            let conn = open_db(db.to_str().ok_or("bad db path")?).map_err(|e| e.to_string())?;
            let dao = InventoryDao::new(&conn);
            let export = dao.export(8)?;
            let json = serde_json::to_string_pretty(&export).map_err(|e| e.to_string())?;
            std::fs::write(&out, json).map_err(|e| e.to_string())?;
            println!("exported");
            Ok(())
        }
    }
}
