use atlaspack_core::{run_pack, run_probe};
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "atlaspack")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Pack {
        #[arg(long)]
        catalog: PathBuf,
        #[arg(long)]
        sprites: PathBuf,
        #[arg(long)]
        set: String,
        #[arg(long)]
        seed: u64,
        #[arg(long)]
        atlas_out: PathBuf,
        #[arg(long)]
        manifest_out: PathBuf,
    },
    Probe {
        #[arg(long)]
        atlas: PathBuf,
        #[arg(long)]
        manifest: PathBuf,
        #[arg(long)]
        glyph: String,
        #[arg(long)]
        frame: u32,
        #[arg(long)]
        u: f64,
        #[arg(long)]
        v: f64,
    },
}

fn main() {
    let cli = Cli::parse();
    let result = match cli.command {
        Commands::Pack {
            catalog,
            sprites,
            set,
            seed,
            atlas_out,
            manifest_out,
        } => run_pack(&catalog, &sprites, &set, seed, &atlas_out, &manifest_out),
        Commands::Probe {
            atlas,
            manifest,
            glyph,
            frame,
            u,
            v,
        } => run_probe(&atlas, &manifest, &glyph, frame, u, v).map(|probe| {
            let line = serde_json::to_string(&probe).expect("probe json");
            println!("{line}");
        }),
    };

    if let Err(err) = result {
        eprintln!("{err}");
        let code = if err.is_oversized() { 2 } else { 1 };
        std::process::exit(code);
    }
}
