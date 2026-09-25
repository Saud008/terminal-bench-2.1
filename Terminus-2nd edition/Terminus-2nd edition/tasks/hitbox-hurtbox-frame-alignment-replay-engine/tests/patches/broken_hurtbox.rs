use crate::model::Hurtbox;

pub fn hurtbox_active(hurtbox: &Hurtbox, frame: u32) -> bool {
    frame >= hurtbox.active_start_frame && frame <= hurtbox.active_end_frame
}
