# Atlas seal contract

`fold-closure` writes `/app/state/closure-lattice.json` and increments `seal_epoch` in `/app/state/seal-epoch.json` by one on every successful fold.

`seal-atlas` requires `seal_epoch` greater than zero. It reads the lattice and writes the atlas with fields `scenario`, `eval_minute`, `active_notam_count`, `sealed_sectors` sorted ascending, and `route_closures` sorted by `flight_id` ascending then `notam_id` ascending.

`atlas_digest` is the SHA-256 hex over the JSON marshaling of a key-sorted payload holding `active_notam_count`, `sealed_sectors`, `eval_minute`, `route_closures`, and `scenario`.

Each `route_closures` row carries `flight_id`, `impact_code`, `detail`, and `notam_id`.
