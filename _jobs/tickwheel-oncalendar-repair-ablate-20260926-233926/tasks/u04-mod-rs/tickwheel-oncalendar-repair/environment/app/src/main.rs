mod civil;
mod cli;
mod engine;
mod errno;
mod spec;
mod table;
mod timestamp;
mod zone;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    std::process::exit(cli::run(&args));
}
