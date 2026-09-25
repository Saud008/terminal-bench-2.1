mod handlers;
mod rpc;
mod state;

use anyhow::Result;
use rpc::{read_message, write_message};
use state::ServerState;

fn main() -> Result<()> {
    let mut state = ServerState::new();
    loop {
        let msg = match read_message() {
            Ok(m) => m,
            Err(e) if e.to_string().contains("EOF") => break,
            Err(e) => return Err(e),
        };
        if let Some(resp) = handlers::dispatch(&mut state, &msg)? {
            write_message(&resp)?;
        }
    }
    Ok(())
}
