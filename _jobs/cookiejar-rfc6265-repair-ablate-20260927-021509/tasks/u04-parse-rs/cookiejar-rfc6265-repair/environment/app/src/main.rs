mod cli;
mod cookie;
mod dump;
mod error;
mod host;
mod jar;
mod psl;
mod time;
mod transcript;
mod url;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    std::process::exit(cli::run(&args));
}
