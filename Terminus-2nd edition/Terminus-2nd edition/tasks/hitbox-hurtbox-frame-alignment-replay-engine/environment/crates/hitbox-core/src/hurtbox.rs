use crate::model::Hurtbox;

pub fn hurtbox_active(hurtbox: &Hurtbox, frame: u32) -> bool {
    let start = hurtbox.active_start_frame + hurtbox.invuln_frames;
    let end = hurtbox.active_end_frame;
    frame >= start && frame <= end
}
