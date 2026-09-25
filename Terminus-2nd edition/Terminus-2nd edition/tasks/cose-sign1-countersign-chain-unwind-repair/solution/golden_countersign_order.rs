use crate::curve_verify::verify_signature;
use crate::model::{
    int_value, map_get, trust_from_payload, value_as_i64, value_as_text, CoseSign1, UnwindStep,
    LABEL_ALG, LABEL_KID,
};
use crate::sig_base::{counter_sig_structure, outer_sig_structure};
use std::collections::BTreeMap;

#[derive(Debug, Clone)]
pub struct OrderedCounter {
    pub original_index: usize,
    pub cs: crate::model::CoseSignature,
}

pub fn order_countersigns(sign1: &CoseSign1) -> Vec<OrderedCounter> {
    sign1
        .countersigns
        .iter()
        .enumerate()
        .map(|(i, cs)| OrderedCounter {
            original_index: i,
            cs: cs.clone(),
        })
        .collect()
}

fn kid_of(cs: &crate::model::CoseSignature) -> Option<String> {
    cs.protected
        .get(&LABEL_KID)
        .and_then(value_as_text)
        .or_else(|| map_get(&cs.unprotected, &int_value(LABEL_KID)).and_then(value_as_text))
}

pub fn unwind_chain(sign1: &CoseSign1) -> Result<(bool, bool, Vec<UnwindStep>), String> {
    let anchors = trust_from_payload(&sign1.payload)?;
    let outer_alg = sign1
        .protected
        .get(&LABEL_ALG)
        .and_then(value_as_i64)
        .ok_or("outer alg missing")?;
    let outer_msg = outer_sig_structure(sign1)?;
    let outer_kid = sign1
        .protected
        .get(&LABEL_KID)
        .and_then(value_as_text)
        .unwrap_or_else(|| "outer".into());
    let outer_pk = anchors.get(&outer_kid).ok_or("outer anchor missing")?;
    let outer_ok = verify_signature(outer_alg, outer_pk, &outer_msg, &sign1.signature)?;

    let mut steps = vec![];
    let mut countersign_ok = true;
    if sign1.countersigns.is_empty() {
        countersign_ok = true;
    }
    for ordered in order_countersigns(sign1) {
        let cs = &ordered.cs;
        let alg = cs
            .protected
            .get(&LABEL_ALG)
            .and_then(value_as_i64)
            .ok_or("cs alg missing")?;
        let kid = kid_of(cs).unwrap_or_else(|| format!("cs{}", ordered.original_index));
        let pk = match anchors.get(&kid) {
            Some(p) => p,
            None => {
                steps.push(UnwindStep {
                    index: ordered.original_index,
                    kid,
                    alg,
                    verify_ok: false,
                });
                countersign_ok = false;
                continue;
            }
        };
        let msg = counter_sig_structure(sign1, cs)?;
        let ok = verify_signature(alg, pk, &msg, &cs.signature).unwrap_or(false);
        if !ok {
            countersign_ok = false;
        }
        steps.push(UnwindStep {
            index: ordered.original_index,
            kid,
            alg,
            verify_ok: ok,
        });
    }
    Ok((outer_ok, countersign_ok, steps))
}

pub fn anchors_from_payload(payload: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, String> {
    trust_from_payload(payload)
}
