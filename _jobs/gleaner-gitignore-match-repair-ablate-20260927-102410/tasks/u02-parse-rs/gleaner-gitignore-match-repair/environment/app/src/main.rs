use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match gleaner::cli::run(&args) {
        Ok(code) => ExitCode::from(code),
        Err(err) => {
            eprintln!("gleaner: {err}");
            ExitCode::from(2)
        }
    }
}
