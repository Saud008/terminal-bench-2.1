use std::fs;
use std::path::Path;

use crate::cbor::canonical;
use crate::cbor::tag24;
use crate::cbor::wire;
use crate::db::audit::AuditStore;
use crate::model::types::{DiagnosticTag, PolicyEnvelope};
use crate::staging::write;

pub fn run(bundle_path: &Path, revalidate: bool) -> Result<(), String> {
    let raw = fs::read(bundle_path).map_err(|e| e.to_string())?;
    let (bundle_id, tags, envelope) = parse_bundle(&raw)?;
    let snapshot = canonical::snapshot_from_bundle(&bundle_id, &tags, &envelope);
    let staged_bytes = write::write_staging(&snapshot)?;
    let store = AuditStore::open()?;
    if revalidate {
        store.record_revalidate(&snapshot)?;
    } else {
        store.record_ingest(&snapshot)?;
    }
    println!(
        "ingested {} ({} bytes staged)",
        snapshot.bundle_id,
        staged_bytes.len()
    );
    Ok(())
}

pub fn parse_bundle(raw: &[u8]) -> Result<(String, Vec<DiagnosticTag>, PolicyEnvelope), String> {
    let mut pos = 0;
    let pairs = wire::decode_map(raw, &mut pos)?;
    if pos != raw.len() {
        return Err("trailing bytes in bundle".into());
    }

    let mut bundle_id = None;
    let mut tags = None;
    let mut envelope = None;
    let mut version = None;

    for (key, value) in pairs {
        let mut vp = 0;
        match key.as_str() {
            "bundle_id" => bundle_id = Some(wire::decode_text(&value, &mut vp)?),
            "diagnostic_tags" => tags = Some(parse_tags(&value)?),
            "envelope" => {
                let (policy, nonce) = tag24::decode_policy_envelope(&value)?;
                envelope = Some(PolicyEnvelope { policy, nonce });
            }
            "version" => version = Some(wire::decode_uint(&value, &mut vp)?),
            other => return Err(format!("unexpected bundle key: {}", other)),
        }
    }

    let bundle_id = bundle_id.ok_or("missing bundle_id")?;
    let tags = tags.ok_or("missing diagnostic_tags")?;
    let envelope = envelope.ok_or("missing envelope")?;
    let version = version.ok_or("missing version")?;
    if version != 1 {
        return Err(format!("unsupported bundle version: {}", version));
    }
    if tags.is_empty() {
        return Err("diagnostic_tags must not be empty".into());
    }

    Ok((bundle_id, tags, envelope))
}

fn parse_tags(encoded: &[u8]) -> Result<Vec<DiagnosticTag>, String> {
    let mut pos = 0;
    let items = wire::decode_array(encoded, &mut pos)?;
    if pos != encoded.len() {
        return Err("trailing bytes in diagnostic_tags".into());
    }
    let mut out = Vec::with_capacity(items.len());
    for item in items {
        let mut ip = 0;
        let pairs = wire::decode_map(&item, &mut ip)?;
        if ip != item.len() {
            return Err("trailing bytes in diagnostic tag item".into());
        }
        let mut label = None;
        let mut tag = None;
        for (k, v) in pairs {
            let mut vp = 0;
            match k.as_str() {
                "label" => label = Some(wire::decode_text(&v, &mut vp)?),
                "tag" => tag = Some(wire::decode_uint(&v, &mut vp)?),
                other => return Err(format!("unexpected diagnostic tag key: {}", other)),
            }
        }
        out.push(DiagnosticTag {
            label: label.ok_or("missing label in diagnostic tag")?,
            tag: tag.ok_or("missing tag in diagnostic tag")?,
        });
    }
    Ok(out)
}
