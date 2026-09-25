use crate::wx_risk_blend::cloud_blend;
use crate::tasking_types::{ImagingRequest, PreemptionEvent, ScenarioBundle, SlotAssignment};
use crate::wx_temporal_pad::windows_overlap_with_setup;
use crate::wx_rank_gate::{contract_rank, should_preempt, sort_requests};
use crate::pass_eligibility::eligible_passes;
use crate::wx_mode_dwell::setup_duration;
use std::collections::BTreeMap;

#[derive(Clone)]
struct OccupiedSlot {
    start: u64,
    end: u64,
    setup_pad: u64,
    request_id: String,
    rank: u32,
    pass_id: String,
    cell_id: String,
}

pub fn resolve_plan(bundle: &ScenarioBundle) -> (Vec<SlotAssignment>, Vec<PreemptionEvent>) {
    let contracts: BTreeMap<_, _> = bundle
        .priority_contracts
        .iter()
        .map(|c| (c.contract_id.clone(), c.clone()))
        .collect();
    let mut requests = bundle.imaging_requests.clone();
    sort_requests(&mut requests, &contracts);
    let mut occupied: Vec<OccupiedSlot> = Vec::new();
    let mut assignments: Vec<SlotAssignment> = Vec::new();
    let mut preemptions: Vec<PreemptionEvent> = Vec::new();
    let mut pass_cursor: BTreeMap<String, u64> = BTreeMap::new();
    let mut last_mode_on_pass: BTreeMap<String, String> = BTreeMap::new();

    for req in requests {
        if let Some(plan) = plan_one(
            &req,
            bundle,
            &contracts,
            &mut occupied,
            &mut pass_cursor,
            &mut last_mode_on_pass,
            &mut preemptions,
            &mut assignments,
        ) {
            assignments.push(plan);
        }
    }
    (assignments, preemptions)
}

fn remove_request(occupied: &mut Vec<OccupiedSlot>, assignments: &mut Vec<SlotAssignment>, request_id: &str) {
    occupied.retain(|slot| slot.request_id != request_id);
    assignments.retain(|a| a.request_id != request_id);
}

fn clear_pass_state(
    pass_id: &str,
    pass_cursor: &mut BTreeMap<String, u64>,
    last_mode: &mut BTreeMap<String, String>,
) {
    pass_cursor.remove(pass_id);
    last_mode.remove(pass_id);
}

fn plan_one(
    req: &ImagingRequest,
    bundle: &ScenarioBundle,
    contracts: &BTreeMap<String, crate::tasking_types::PriorityContract>,
    occupied: &mut Vec<OccupiedSlot>,
    pass_cursor: &mut BTreeMap<String, u64>,
    last_mode: &mut BTreeMap<String, String>,
    preemptions: &mut Vec<PreemptionEvent>,
    assignments: &mut Vec<SlotAssignment>,
) -> Option<SlotAssignment> {
    let rank = contract_rank(contracts, &req.contract_id);
    let passes = eligible_passes(req, &bundle.pass_windows);
    let mut best: Option<(SlotAssignment, f64)> = None;

    for pass in passes {
        if let Some(idx) = occupied.iter().position(|slot| {
            slot.pass_id == pass.pass_id && slot.cell_id == req.cell_id
        }) {
            let slot = occupied[idx].clone();
            if should_preempt(rank, slot.rank) {
                preemptions.push(PreemptionEvent {
                    displaced_request_id: slot.request_id.clone(),
                    winner_request_id: req.request_id.clone(),
                    pass_id: pass.pass_id.clone(),
                });
                remove_request(occupied, assignments, &slot.request_id);
                clear_pass_state(&pass.pass_id, pass_cursor, last_mode);
            } else {
                continue;
            }
        }

        let warm = last_mode
            .get(&pass.pass_id)
            .map(|m| m == &req.mode)
            .unwrap_or(false);
        let setup = setup_duration(&bundle.sensor_modes, &req.mode, warm);
        let cursor = *pass_cursor.get(&pass.pass_id).unwrap_or(&pass.start_sec);
        let eff_start = cursor + setup;
        let eff_end = eff_start + req.imaging_duration_sec;
        if eff_end > pass.end_sec {
            continue;
        }

        let forecast = bundle
            .cloud_forecasts
            .iter()
            .find(|f| f.pass_id == pass.pass_id && f.cell_id == req.cell_id)
            .cloned()
            .unwrap_or(crate::tasking_types::CloudForecast {
                pass_id: pass.pass_id.clone(),
                cell_id: req.cell_id.clone(),
                risk_score: 1.0,
                coverage_factor: 0.0,
            });
        let composite = cloud_blend(&forecast);

        let mut clash_idx: Option<usize> = None;
        for (idx, slot) in occupied.iter().enumerate() {
            if windows_overlap_with_setup(
                eff_start,
                eff_end,
                setup,
                slot.start,
                slot.end,
                slot.setup_pad,
            ) {
                clash_idx = Some(idx);
                break;
            }
        }

        if let Some(idx) = clash_idx {
            let slot = occupied[idx].clone();
            if should_preempt(rank, slot.rank) {
                preemptions.push(PreemptionEvent {
                    displaced_request_id: slot.request_id.clone(),
                    winner_request_id: req.request_id.clone(),
                    pass_id: pass.pass_id.clone(),
                });
                remove_request(occupied, assignments, &slot.request_id);
                clear_pass_state(&pass.pass_id, pass_cursor, last_mode);
            } else {
                continue;
            }
        }

        let candidate = SlotAssignment {
            request_id: req.request_id.clone(),
            pass_id: pass.pass_id.clone(),
            orbit_id: pass.orbit_id.clone(),
            cell_id: req.cell_id.clone(),
            mode: req.mode.clone(),
            setup_sec: setup,
            effective_start_sec: eff_start,
            effective_end_sec: eff_end,
            cloud_composite: composite,
            preempt_rank: rank,
        };

        match &best {
            None => best = Some((candidate, composite)),
            Some((_, score)) if composite < *score => best = Some((candidate, composite)),
            _ => {}
        }
    }

    if let Some((plan, _)) = best {
        occupied.push(OccupiedSlot {
            start: plan.effective_start_sec,
            end: plan.effective_end_sec,
            setup_pad: plan.setup_sec,
            request_id: plan.request_id.clone(),
            rank: plan.preempt_rank,
            pass_id: plan.pass_id.clone(),
            cell_id: plan.cell_id.clone(),
        });
        pass_cursor.insert(
            plan.pass_id.clone(),
            plan.effective_end_sec + plan.setup_sec,
        );
        last_mode.insert(plan.pass_id.clone(), plan.mode.clone());
        Some(plan)
    } else {
        None
    }
}
