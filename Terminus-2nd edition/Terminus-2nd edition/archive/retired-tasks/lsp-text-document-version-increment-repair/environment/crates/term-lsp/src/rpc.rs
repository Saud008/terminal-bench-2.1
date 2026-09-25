use std::io::{self, Read, Write};

use anyhow::{Context, Result};
use serde_json::Value;

pub fn read_message() -> Result<Value> {
    let mut stdin = io::stdin().lock();
    let mut header = String::new();
    let mut content_length: Option<usize> = None;
    loop {
        header.clear();
        let mut byte = [0u8; 1];
        let mut line = Vec::new();
        loop {
            stdin.read_exact(&mut byte).context("EOF")?;
            if byte[0] == b'\n' {
                break;
            }
            line.push(byte[0]);
        }
        let line_str = String::from_utf8(line)?.trim_end_matches('\r').to_string();
        if line_str.is_empty() {
            break;
        }
        if let Some(rest) = line_str.strip_prefix("Content-Length: ") {
            content_length = Some(rest.trim().parse()?);
        }
    }
    let len = content_length.context("missing Content-Length")?;
    let mut body = vec![0u8; len];
    stdin.read_exact(&mut body)?;
    Ok(serde_json::from_slice(&body)?)
}

pub fn write_message(value: &Value) -> Result<()> {
    let body = serde_json::to_vec(value)?;
    let mut stdout = io::stdout().lock();
    write!(stdout, "Content-Length: {}\r\n\r\n", body.len())?;
    stdout.write_all(&body)?;
    stdout.flush()?;
    Ok(())
}
