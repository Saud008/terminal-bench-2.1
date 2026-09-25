# Rig slot constraints

Mount inventory slots map rig_slot to camera_serial and allowed_lens_ids.

A capture is valid only when:

- capture.rig_slot equals slot.slot
- capture.camera_serial equals slot.camera_serial
- capture.lens_id is listed in slot.allowed_lens_ids

Reject with rig_slot_mismatch when slot or serial disagree.

Reject with lens_not_allowed when lens_id is not allowed for the slot.
