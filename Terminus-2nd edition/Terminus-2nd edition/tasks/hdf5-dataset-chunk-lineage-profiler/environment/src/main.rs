use s5lineage::hdclp_cli::Cli;

fn main() {
    if let Err(e) = Cli::run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
