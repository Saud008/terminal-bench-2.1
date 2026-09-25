use crate::types::MembraneBatch;
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct NormParams {
    pub alpha: f64,
    pub beta: f64,
    pub p_base: f64,
    pub t_ref: f64,
    pub q_ref: f64,
}

pub fn initial_bases(batches: &[MembraneBatch]) -> HashMap<String, f64> {
    let mut out = HashMap::new();
    for b in batches {
        if let Some(p) = b.p_base {
            out.insert(b.batch_id.clone(), p);
        }
    }
    out
}

pub fn batch_for_hour(hour: u32, batches: &[MembraneBatch]) -> Option<String> {
    for b in batches {
        if hour > b.active_from_hour && hour < b.active_until_hour {
            return Some(b.batch_id.clone());
        }
    }
    None
}

pub fn resolve_norm(batch_id: &str, batches: &[MembraneBatch]) -> Result<NormParams, String> {
    let map: HashMap<String, &MembraneBatch> = batches.iter().map(|b| (b.batch_id.clone(), b)).collect();
    if !map.contains_key(batch_id) {
        return Err(format!("unknown batch {batch_id}"));
    }
    Ok(NormParams {
        alpha: pick_field(&map, batch_id, "alpha"),
        beta: pick_field(&map, batch_id, "beta"),
        p_base: pick_field(&map, batch_id, "p_base"),
        t_ref: pick_field(&map, batch_id, "t_ref"),
        q_ref: pick_field(&map, batch_id, "q_ref"),
    })
}

fn pick_field(map: &HashMap<String, &MembraneBatch>, batch_id: &str, field: &str) -> f64 {
    let mut cur = batch_id.to_string();
    loop {
        let Some(batch) = map.get(cur.as_str()) else {
            break;
        };
        let val = match field {
            "alpha" => batch.alpha,
            "beta" => batch.beta,
            "p_base" => batch.p_base,
            "t_ref" => batch.t_ref,
            "q_ref" => batch.q_ref,
            _ => None,
        };
        if let Some(v) = val {
            return v;
        }
        match &batch.parent_batch_id {
            Some(p) => cur = p.clone(),
            None => break,
        }
    }
    match field {
        "alpha" | "beta" => 1.0,
        "p_base" => 0.0,
        "t_ref" => 25.0,
        _ => 100.0,
    }
}
