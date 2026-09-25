mod lib;
fn main() { if let Err(e) = cli::run(std::env::args().skip(1).collect()) { eprintln!("{e}"); std::process::exit(1); } }
