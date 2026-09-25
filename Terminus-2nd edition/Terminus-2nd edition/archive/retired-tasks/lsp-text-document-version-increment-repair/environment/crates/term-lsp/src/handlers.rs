use anyhow::Result;
use docmodel::ContentChange;
use docsync::{handle_did_change, handle_did_close, handle_did_open};
use docexport::export_snapshot;
use serde_json::{json, Value};

use crate::state::ServerState;

pub fn dispatch(state: &mut ServerState, msg: &Value) -> Result<Option<Value>> {
    if msg.get("method").is_none() {
        return Ok(None);
    }
    let method = msg["method"].as_str().unwrap_or("");
    let id = msg.get("id").cloned();
    match method {
        "initialize" => {
            state.initialized = true;
            Ok(Some(response(id, json!({"capabilities": {"textDocumentSync": 2}}))))
        }
        "initialized" => Ok(None),
        "shutdown" => Ok(Some(response(id, Value::Null))),
        "exit" => Ok(None),
        "textDocument/didOpen" => {
            let params = &msg["params"];
            let uri = params["textDocument"]["uri"].as_str().unwrap_or("").to_string();
            let text = params["textDocument"]["text"].as_str().unwrap_or("").to_string();
            let version = params["textDocument"]["version"].as_i64().unwrap_or(0) as i32;
            let doc = handle_did_open(uri.clone(), text, version);
            state.docs.insert(uri, doc);
            Ok(None)
        }
        "textDocument/didChange" => {
            let params = &msg["params"];
            let uri = params["textDocument"]["uri"].as_str().unwrap_or("").to_string();
            let version = params["textDocument"]["version"].as_i64().unwrap_or(0) as i32;
            let changes: Vec<ContentChange> =
                serde_json::from_value(params["contentChanges"].clone()).unwrap_or_default();
            if let Some(doc) = state.docs.get_mut(&uri) {
                handle_did_change(doc, version, changes)?;
            }
            Ok(None)
        }
        "textDocument/didClose" => {
            let params = &msg["params"];
            let uri = params["textDocument"]["uri"].as_str().unwrap_or("").to_string();
            if let Some(doc) = state.docs.get_mut(&uri) {
                handle_did_close(doc)?;
            }
            Ok(None)
        }
        "workspace/executeCommand" => {
            let params = &msg["params"];
            let command = params["command"].as_str().unwrap_or("");
            if command == "doclint.exportSnapshot" {
                let uri = params["arguments"][0].as_str().unwrap_or("").to_string();
                let doc = state
                    .docs
                    .get_mut(&uri)
                    .ok_or_else(|| anyhow::anyhow!("unknown doc"))?;
                let snap = export_snapshot(doc)?;
                let result = serde_json::to_value(&snap)?;
                return Ok(Some(response(id, result)));
            }
            Ok(Some(response(id, json!({"error": "unknown command"}))))
        }
        _ => Ok(None),
    }
}

fn response(id: Option<Value>, result: Value) -> Value {
    json!({
        "jsonrpc": "2.0",
        "id": id,
        "result": result,
    })
}
