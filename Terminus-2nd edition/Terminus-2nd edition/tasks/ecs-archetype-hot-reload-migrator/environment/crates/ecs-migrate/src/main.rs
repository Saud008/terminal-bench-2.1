use anyhow::{bail, Context, Result};
use std::env;
use std::path::PathBuf;

fn main() -> Result<()> {
    let mut args = env::args().skip(1);
    let Some(cmd) = args.next() else {
        bail!("usage: ecs-migrate apply --db PATH --chunks PATH --layout PATH --journal PATH --report PATH");
    };
    if cmd != "apply" {
        bail!("unknown command {cmd}");
    }
    let mut db = None;
    let mut chunks = None;
    let mut layout = None;
    let mut journal = None;
    let mut report = None;
    while let Some(flag) = args.next() {
        let value = args
            .next()
            .with_context(|| format!("missing value for {flag}"))?;
        match flag.as_str() {
            "--db" => db = Some(PathBuf::from(value)),
            "--chunks" => chunks = Some(PathBuf::from(value)),
            "--layout" => layout = Some(PathBuf::from(value)),
            "--journal" => journal = Some(PathBuf::from(value)),
            "--report" => report = Some(PathBuf::from(value)),
            other => bail!("unknown flag {other}"),
        }
    }
    let (db, chunks, layout, journal, report) = match (db, chunks, layout, journal, report) {
        (Some(db), Some(chunks), Some(layout), Some(journal), Some(report)) => {
            (db, chunks, layout, journal, report)
        }
        _ => bail!("missing required apply flags"),
    };
    ecs_core::apply_migration(&db, &chunks, &layout, &journal, &report)?;
    Ok(())
}
