# Campaign binding contract

`bind-campaign` writes `/app/state/campaign-binding.json` containing `engine`, `scenario`, `notams`, `sectors`, `flights`, `airways`, `fix_points`, `policy`, and `binding_digest`.

`binding_digest` is the SHA-256 hex over the JSON marshaling of a key-sorted payload map holding `policy`, `scenario`, `notams`, `sectors`, `flights`, `airways`, and `fix_points`. The policy and the fix-point table both participate in the digest; a binding that omits either does not reproduce the reference digest.

Campaign inputs live under `FIXTURE_DIR/scenarios/SCENARIO/`: `notams.jsonl`, `sectors.json`, `flights.jsonl`, `fix_points.json`, `airways.json`, and `policy.json`.
