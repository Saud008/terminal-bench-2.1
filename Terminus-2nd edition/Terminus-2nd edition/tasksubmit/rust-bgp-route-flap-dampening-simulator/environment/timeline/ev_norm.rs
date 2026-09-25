//! Admit stage: read BGP update NDJSON, validate chronology, and build scenario-lock snapshot.
use crate::feed_chrono;use crate::feed_reader;
use crate::lock_store;
use crate::peer_table;
use crate::route_model::ScenarioSpec;
use std::fs;
use std::path::Path;

pub fn compile_scenario(scenario_id: &str, root: &str) -> Result<(), String> {
    let spec = load_spec(root, scenario_id)?;
    let feed_path = Path::new(root).join(&spec.feed_path);
    let raw = fs::read(&feed_path).map_err(|e| e.to_string())?;
    let mut events = feed_reader::parse_lines(&raw)?;
    feed_chrono::assert_peer_monotonic(&events)?;
    events = feed_chrono::dedupe(events);
    feed_chrono::sort_feed(&mut events);
    let peer_table = peer_table::load_table(root, &spec.peers)?;
    let scenario_lock =
        lock_store::build_lock(scenario_id, &spec.feed_path, &raw, events.len(), peer_table);
    lock_store::persist(&scenario_lock)
}

fn load_spec(root: &str, scenario_id: &str) -> Result<ScenarioSpec, String> {
    let path = Path::new(root)
        .join("scenarios")
        .join(format!("{scenario_id}.json"));
    let spec: ScenarioSpec =
        serde_json::from_str(&fs::read_to_string(path).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
    if spec.scenario_id != scenario_id {
        return Err("scenario_id mismatch".into());
    }
    Ok(spec)
}

pub fn load_events_from_root(root: &str, relpath: &str) -> Result<Vec<crate::route_model::FeedEvent>, String> {
    let raw = fs::read(Path::new(root).join(relpath)).map_err(|e| e.to_string())?;
    let mut events = feed_reader::parse_lines(&raw)?;
    feed_chrono::assert_peer_monotonic(&events)?;
    events = feed_chrono::dedupe(events);
    feed_chrono::sort_feed(&mut events);
    Ok(events)
}
