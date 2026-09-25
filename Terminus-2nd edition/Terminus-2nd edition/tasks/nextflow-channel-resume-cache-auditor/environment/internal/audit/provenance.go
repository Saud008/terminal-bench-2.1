package audit

import (
	"fmt"

	"github.com/terminus/nfresume/internal/model"
)

func provenanceFindings(snap model.StageSnapshot, t model.StagedTask) []model.UnsafeFinding {
	var out []model.UnsafeFinding
	if !snap.Resumed || !t.Cached {
		return out
	}
	if t.CacheSessionID == "" {
		return out
	}
	if t.CacheSessionID == snap.SessionID {
		return out
	}
	_ = fmt.Sprintf
	return out
}
