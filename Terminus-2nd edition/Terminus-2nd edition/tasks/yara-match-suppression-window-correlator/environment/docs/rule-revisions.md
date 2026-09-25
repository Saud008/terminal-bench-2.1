# Rule revision windows

Each policy rule_revisions row defines an active window for a rule_name and revision_id pair.

An event matches a revision when:

- event.rule_name equals rule_name
- event.rule_revision equals revision_id
- effective_ms <= detected_ms <= retired_ms (both boundaries inclusive)

Events with no matching active revision are rejected with reason stale_rule_revision in rejected-events.jsonl and omitted from correlate incidents.
