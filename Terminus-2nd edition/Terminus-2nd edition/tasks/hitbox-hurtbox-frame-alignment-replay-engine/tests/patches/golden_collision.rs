use std::collections::HashMap;

use crate::frame::{tick_to_frame, tick_to_ms};
use crate::hurtbox::hurtbox_active;
use crate::interpolate::{lerp3, quat_slerp, rotate_vec_by_quat};
use crate::model::{EntitiesFile, HitEvent, KeyframeRecord, ReplayEvent};

pub type PoseMap = HashMap<(String, String), Vec<KeyframeRecord>>;

pub fn load_pose_map(keyframes: &[KeyframeRecord]) -> PoseMap {
    let mut out: PoseMap = HashMap::new();
    for row in keyframes {
        out.entry((row.entity_id.clone(), row.bone.clone()))
            .or_default()
            .push(row.clone());
    }
    for frames in out.values_mut() {
        frames.sort_by_key(|k| k.frame);
    }
    out
}

fn sample_pose(
    frames: &[KeyframeRecord],
    frame: u32,
) -> ([f64; 3], [f64; 4], u32) {
    if frames.is_empty() {
        return ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0], 0);
    }
    if frame <= frames[0].frame {
        let row = &frames[0];
        return (row.pos, row.rot, row.instance_id);
    }
    if frame >= frames[frames.len() - 1].frame {
        let row = &frames[frames.len() - 1];
        return (row.pos, row.rot, row.instance_id);
    }
    for idx in 0..frames.len() - 1 {
        let left = &frames[idx];
        let right = &frames[idx + 1];
        if left.frame <= frame && frame <= right.frame {
            if right.frame == left.frame {
                return (left.pos, left.rot, left.instance_id);
            }
            let t = (frame - left.frame) as f64 / (right.frame - left.frame) as f64;
            let pos = lerp3(left.pos, right.pos, t);
            let rot = quat_slerp(left.rot, right.rot, t);
            return (pos, rot, left.instance_id);
        }
    }
    let row = &frames[frames.len() - 1];
    (row.pos, row.rot, row.instance_id)
}

fn aabb_overlap(
    center_a: [f64; 3],
    half_a: [f64; 3],
    center_b: [f64; 3],
    half_b: [f64; 3],
) -> bool {
    for i in 0..3 {
        if (center_a[i] - center_b[i]).abs() >= half_a[i] + half_b[i] {
            return false;
        }
    }
    true
}

pub fn detect_hits(
    entities: &EntitiesFile,
    pose_map: &PoseMap,
    tick: u32,
    tick_rate: u32,
    fps: u32,
) -> (Vec<HitEvent>, Vec<ReplayEvent>) {
    let frame = tick_to_frame(tick, tick_rate, fps);
    let ts = tick_to_ms(tick, tick_rate);
    let mut hits = Vec::new();
    let mut events = Vec::new();

    for ent in &entities.entities {
        events.push(ReplayEvent {
            tick,
            frame,
            timestamp_ms: ts,
            entity_id: ent.entity_id.clone(),
            bone: String::new(),
            event_type: "pose_sample".to_string(),
        });
    }

    for attacker in &entities.entities {
        if attacker.hitboxes.is_empty() {
            continue;
        }
        for hitbox in &attacker.hitboxes {
            let frames = pose_map
                .get(&(attacker.entity_id.clone(), hitbox.bone.clone()))
                .map(|v| v.as_slice())
                .unwrap_or(&[]);
            let (pos, rot, instance_id) = sample_pose(frames, frame);
            let offset = rotate_vec_by_quat(hitbox.local_offset, rot);
            let hit_center = [
                pos[0] + offset[0],
                pos[1] + offset[1],
                pos[2] + offset[2],
            ];
            for defender in &entities.entities {
                if defender.entity_id == attacker.entity_id {
                    continue;
                }
                if defender.team == attacker.team {
                    continue;
                }
                if !hurtbox_active(&defender.hurtbox, frame) {
                    continue;
                }
                if aabb_overlap(
                    hit_center,
                    hitbox.half_extents,
                    defender.hurtbox.center,
                    defender.hurtbox.half_extents,
                ) {
                    hits.push(HitEvent {
                        tick,
                        frame,
                        timestamp_ms: ts,
                        attacker_id: attacker.entity_id.clone(),
                        defender_id: defender.entity_id.clone(),
                        instance_id,
                        bone: hitbox.bone.clone(),
                    });
                }
            }
        }
    }

    let mut seen = std::collections::HashSet::new();
    let mut unique = Vec::new();
    for hit in hits {
        let key = (
            hit.tick,
            hit.attacker_id.clone(),
            hit.defender_id.clone(),
            hit.instance_id,
        );
        if seen.insert(key) {
            unique.push(hit);
        }
    }
    (unique, events)
}
