use minizdecode::{DecodeError, decompress_zlib};
use std::env;
use std::fs;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: minizdecode decompress --input PATH --output PATH --report PATH --staging PATH");
        process::exit(1);
    }
    if args[1] != "decompress" {
        eprintln!("unknown subcommand");
        process::exit(1);
    }
    let input = flag(&args, "--input").unwrap_or_else(|| usage());
    let output = flag(&args, "--output").unwrap_or_else(|| usage());
    let report = flag(&args, "--report").unwrap_or_else(|| usage());
    let staging = flag(&args, "--staging").unwrap_or_else(|| usage());
    match run(&input, &output, &report, &staging) {
        Ok(()) => process::exit(0),
        Err(e) => {
            eprintln!("{e}");
            match e {
                DecodeError::Checksum(_) => process::exit(2),
                _ => process::exit(1),
            }
        }
    }
}

fn flag(args: &[String], name: &str) -> Option<String> {
    args.iter()
        .position(|a| a == name)
        .and_then(|i| args.get(i + 1))
        .cloned()
}

fn usage() -> ! {
    eprintln!("missing required flag");
    process::exit(1);
}

fn run(input: &str, output: &str, report: &str, staging: &str) -> Result<(), DecodeError> {
    let raw = fs::read(input).map_err(|e| DecodeError::Io(e.to_string()))?;
    let result = decompress_zlib(&raw)?;
    minizdecode::staging::write_staging(staging, input, &result.staging)
        .map_err(|e| DecodeError::Io(e))?;
    let rep = minizdecode::export::write_outputs(
        input,
        output,
        report,
        &result.output,
        result.expected_adler,
        result.staging.block_count,
    )
    .map_err(|e| DecodeError::Io(e))?;
    if !rep.ok {
        return Err(DecodeError::Checksum("adler mismatch".into()));
    }
    Ok(())
}
