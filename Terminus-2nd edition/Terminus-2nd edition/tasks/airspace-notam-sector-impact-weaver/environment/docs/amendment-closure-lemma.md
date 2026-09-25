# Amendment closure lemma

`close-chronology` reads the campaign binding and writes `/app/state/chronology-closure.json` with `active_notams` and `eval_minute` copied from policy.

Before any temporal test, close the NOTAM set over `series_id`: for each `series_id`, keep exactly one row, the one with the maximum `amendment` integer. Every lower amendment for the same `series_id` is discarded. Keeping the first-seen row instead of the maximum amendment breaks the closure and the reference digests.

After the amendment closure, retain only rows whose activation window contains `eval_minute` per `chronology-window-lemma.md`.
