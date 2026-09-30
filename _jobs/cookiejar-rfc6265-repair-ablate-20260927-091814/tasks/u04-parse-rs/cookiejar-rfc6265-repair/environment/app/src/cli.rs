use crate::dump;
use crate::jar::Jar;
use crate::psl::List;
use crate::transcript::{self, Command};
use std::io::{self, BufWriter, Read, Write};

const USAGE: &str = "usage: crumbjar replay <transcript | ->";

pub fn run(args: &[String]) -> i32 {
    let source = match args {
        [cmd, src] if cmd == "replay" => src,
        [flag] if flag == "--version" => {
            println!("crumbjar {}", env!("CARGO_PKG_VERSION"));
            return 0;
        }
        _ => {
            eprintln!("{USAGE}");
            return 2;
        }
    };

    let text = match read_source(source) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("crumbjar: {source}: {e}");
            return 1;
        }
    };
    let commands = match transcript::parse(&text) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("crumbjar: {e}");
            return 1;
        }
    };

    let mut jar = Jar::new(List::builtin());
    let stdout = io::stdout();
    let mut out = BufWriter::new(stdout.lock());
    if let Err(e) = replay(&mut jar, commands, &mut out).and_then(|_| out.flush()) {
        eprintln!("crumbjar: write error: {e}");
        return 1;
    }
    0
}

fn read_source(source: &str) -> io::Result<String> {
    if source == "-" {
        let mut s = String::new();
        io::stdin().read_to_string(&mut s)?;
        Ok(s)
    } else {
        std::fs::read_to_string(source)
    }
}

fn replay<W: Write>(jar: &mut Jar, commands: Vec<Command>, out: &mut W) -> io::Result<()> {
    for cmd in commands {
        match cmd {
            Command::At(t) => jar.set_clock(t),
            Command::Set(url, header) => jar.set_cookie(&url, &header),
            Command::Get(url) => {
                let header = jar.cookie_header(&url);
                writeln!(out, "{}\t{}", url.raw, header)?;
            }
            Command::Dump => dump::write(out, jar)?,
        }
    }
    Ok(())
}
