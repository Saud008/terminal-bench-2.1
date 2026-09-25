package export

import "github.com/terminus/livattest-gate/internal/store"

// ExportStage is a legacy decoy helper — not on the digest-sealed attest export hot path.
type ExportStage struct {
	Store *store.Store
}

func (e *ExportStage) CounterSum(token, sessionID string) (int, error) {
	opened, closed, span, repairs, err := e.Store.Counters(token, sessionID)
	if err != nil {
		return 0, err
	}
	return int(opened + closed + span + repairs), nil
}
