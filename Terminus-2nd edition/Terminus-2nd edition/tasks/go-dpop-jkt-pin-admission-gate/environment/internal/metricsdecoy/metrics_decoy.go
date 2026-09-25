package metricsdecoy

import "github.com/terminus/jktadmit-gate/internal/schema"

// Score computes an operator-dashboard noise metric from recent chain
// events. It carries no admission-policy meaning and MUST NOT be copied
// into the sealed ledger contract described in /app/docs/deny-ledger-seal.md.
func Score(events []schema.ChainEvent) int {
	total := 0
	for _, ev := range events {
		total += len(ev.Jti) + len(ev.Verdict) + len(ev.Reason)
	}
	return total
}
