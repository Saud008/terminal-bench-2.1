use std::fs;

use std::path::PathBuf;



use clap::{Parser, Subcommand};



use archecore::{migrate_world, replay_world, run_query, run_query_batch, QueryBatchSpec, WorldSpec};

use archecore::export::publish;



#[derive(Parser)]

#[command(name = "archectl")]

struct Cli {

    #[command(subcommand)]

    command: Commands,

}



#[derive(Subcommand)]

enum Commands {

    ReplayWorld {

        #[arg(long)]

        world: PathBuf,

        #[arg(long)]

        seed: Option<String>,

    },

    Migrate {

        #[arg(long)]

        world: PathBuf,

        #[arg(long)]

        export: PathBuf,

        #[arg(long)]

        seed: Option<String>,

    },

    Query {

        #[arg(long)]

        world: PathBuf,

        #[arg(long)]

        components: String,

        #[arg(long)]

        export: PathBuf,

        #[arg(long)]

        seed: Option<String>,

    },

    QueryBatch {

        #[arg(long)]

        batch: PathBuf,

        #[arg(long)]

        export: PathBuf,

        #[arg(long)]

        seed: Option<String>,

    },

    PublishMigrate {

        #[arg(long)]

        snapshot: PathBuf,

        #[arg(long)]

        export: PathBuf,

    },

}



fn load_world(path: &PathBuf) -> WorldSpec {

    let data = fs::read_to_string(path).expect("read world");

    serde_json::from_str(&data).expect("parse world")

}



fn default_seed() -> String {

    let data = fs::read_to_string("/app/fixtures/seeds.json").unwrap_or_else(|_| "[]".into());

    let seeds: Vec<String> = serde_json::from_str(&data).unwrap_or_default();

    seeds.first().cloned().unwrap_or_else(|| "alpha-7".into())

}



fn write_json<T: serde::Serialize>(path: &PathBuf, value: &T) {

    if let Some(parent) = path.parent() {

        fs::create_dir_all(parent).ok();

    }

    fs::write(path, serde_json::to_string_pretty(value).unwrap()).expect("write export");

}



fn parse_component_ids(raw: &str) -> Vec<u16> {

    raw.split(',')

        .filter(|s| !s.is_empty())

        .map(|s| s.parse().expect("component id"))

        .collect()

}



fn main() {

    let cli = Cli::parse();

    match cli.command {

        Commands::ReplayWorld { world, seed } => {

            let seed = seed.unwrap_or_else(default_seed);

            let spec = load_world(&world);

            if let Err(err) = replay_world(&spec, &seed) {

                eprintln!("replay-world failed: {err}");

                std::process::exit(1);

            }

        }

        Commands::Migrate { world, export, seed } => {

            let seed = seed.unwrap_or_else(default_seed);

            let spec = load_world(&world);

            let out = migrate_world(&spec, &seed);

            write_json(&export, &out);

        }

        Commands::Query {

            world,

            components,

            export,

            seed,

        } => {

            let seed = seed.unwrap_or_else(default_seed);

            let spec = load_world(&world);

            let ids = parse_component_ids(&components);

            let out = run_query(&spec, &seed, &ids);

            write_json(&export, &out);

        }

        Commands::QueryBatch { batch, export, seed } => {

            let seed = seed.unwrap_or_else(default_seed);

            let data = fs::read_to_string(&batch).expect("read batch");

            let batch_spec: QueryBatchSpec = serde_json::from_str(&data).expect("parse batch");

            let mut loaded = Vec::new();

            let mut id_vecs = Vec::new();

            for step in &batch_spec.steps {

                let spec = load_world(&PathBuf::from(&step.world_path));

                id_vecs.push(step.components.clone());

                loaded.push(spec);

            }

            let pairs: Vec<(&WorldSpec, &[u16])> = loaded

                .iter()

                .zip(id_vecs.iter())

                .map(|(spec, ids)| (spec, ids.as_slice()))

                .collect();

            let out = run_query_batch(&pairs, &seed);

            write_json(&export, &out);

        }

        Commands::PublishMigrate { snapshot, export } => {

            let out = publish::publish_migrate(snapshot.to_str().expect("snapshot path"))

                .expect("publish migrate");

            write_json(&export, &out);

        }

    }

}

