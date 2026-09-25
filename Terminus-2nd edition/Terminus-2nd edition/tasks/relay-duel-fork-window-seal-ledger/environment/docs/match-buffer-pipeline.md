# Match buffer pipeline

admit-log writes /app/state/match-buffer.json with arena, scenario, messages, and policy.

fold-branches adds matches map keyed by branch key with answer_ts_ms, end_ts_ms, disposition, answered flag, and stamps match_seal.

score-windows adds score_band per match, refreshes match_seal, and writes score-window-report.json.

TB3_FIXTURE_DIR may point at /opt/verifier-fixtures/duelctl for hidden scenarios.
