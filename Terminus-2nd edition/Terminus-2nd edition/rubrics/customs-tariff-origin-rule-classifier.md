# Platform rubric — customs-tariff-origin-rule-classifier

**Task folder:** tasks/customs-tariff-origin-rule-classifier/

Agent parses shipment manifests into /app/var/ledger/tariff.db via parse-shipment, +3
Agent normalizes HS codes to ten digit HS10 in staging snapshot, +3
Agent computes regional value bps from declared origin BOM share rows, +3
Agent validates certificates with inclusive issued_on and expires_on windows, +3
Agent picks preferential agreement by lowest priority then lexicographic code, +3
Agent blocks write-atlas until parse_pass in origin-pass.json is positive, +3
Agent requires score-origin staging file before write-atlas export, +3
Agent publishes sorted classifications at /app/output/tariff-classifications.json, +2
Agent appends origin-audit.jsonl rows with agreement_code and rvc_bps fields, +2
Agent rebuilds originctl via verifier-rebuild.sh before subprocess CLI checks, +2
Agent pads HS codes to eight digits only leaving HS10 contract unmet, -3
Agent sums foreign BOM share instead of originating share for RVC threshold, -3
Agent treats certificate expiry day as invalid using exclusive end date, -3
Agent picks highest priority number agreement instead of lowest precedence, -3
Agent emits preferential treatment when RVC is below agreement rvc_min_bps, -3
Agent skips score-origin yet still writes tariff atlas export file, -3
