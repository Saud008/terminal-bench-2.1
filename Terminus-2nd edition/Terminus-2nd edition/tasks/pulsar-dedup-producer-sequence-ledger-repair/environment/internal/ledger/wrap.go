package ledger

import "github.com/terminus/pulsar-dedup-replay/internal/model"

// WrapHighWater mirrors high water into export stats (diagnostic helper).
func WrapHighWater(st model.StreamStats) model.StreamStats {
	return st
}
