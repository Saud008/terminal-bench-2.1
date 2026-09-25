use crate::engine_decay;
use crate::peer_table;
use crate::route_model::{FeedEvent, FeedKind, PeerDampening, PrefixLedger};
use std::collections::BTreeMap;

pub fn step(
    entries: &mut BTreeMap<String, PrefixLedger>,
    table: &BTreeMap<String, PeerDampening>,
    ev: &FeedEvent,
) {
    let key = crate::route_model::ledger_key(&ev.peer, &ev.prefix);
    let row = peer_table::row_for(table, &ev.peer);
    let slot = entries.entry(key).or_insert_with(|| PrefixLedger {
        penalty: 0,
        advertised: false,
        suppressed: false,
        flap_count: 0,
        peak_penalty: 0,
        last_ts_ms: 0,
        stable_at_ms: None,
    });
    slot.penalty = engine_decay::apply_decay(slot.penalty, slot.last_ts_ms, ev.ts_ms, row.half_life_ms);
    slot.last_ts_ms = ev.ts_ms;
    match ev.kind {
        FeedKind::Announce => on_announce(slot, &row),
        FeedKind::Withdraw => on_withdraw(slot, &row),
    }
    slot.peak_penalty = slot.peak_penalty.max(slot.penalty);
    maybe_stable(slot, &row);
}

fn on_announce(slot: &mut PrefixLedger, row: &PeerDampening) {
    if slot.advertised {
        return;
    }
    if slot.suppressed && slot.penalty >= row.reuse_threshold {
        return;
    }
    slot.advertised = true;
    if slot.penalty >= row.suppress_threshold {
        slot.suppressed = true;
    }
}

fn on_withdraw(slot: &mut PrefixLedger, row: &PeerDampening) {
    if !slot.advertised {
        return;
    }
    slot.advertised = false;
    slot.penalty = (slot.penalty + row.flap_penalty).min(row.max_penalty);
    slot.flap_count += 1;
    if slot.penalty >= row.suppress_threshold {
        slot.suppressed = true;
    }
}

fn maybe_stable(slot: &mut PrefixLedger, row: &PeerDampening) {
    if !slot.advertised && slot.penalty < row.reuse_threshold && slot.stable_at_ms.is_none() {
        slot.stable_at_ms = Some(slot.last_ts_ms);
    }
}
