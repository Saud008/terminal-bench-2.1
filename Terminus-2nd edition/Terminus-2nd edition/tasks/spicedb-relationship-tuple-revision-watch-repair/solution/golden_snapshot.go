package check

import (
	"github.com/example/spicedb-relation-watch/internal/store"
)

// SnapshotPolicy decides whether check reads live store or cached snapshot file.
type SnapshotPolicy struct {
	Threshold int64
}

// NewSnapshotPolicy creates a lag threshold policy.
func NewSnapshotPolicy(threshold int64) *SnapshotPolicy {
	return &SnapshotPolicy{Threshold: threshold}
}

// ShouldUseStale returns true when check should read stale snapshot bytes.
func (p *SnapshotPolicy) ShouldUseStale(headRevision, atRevision int64) bool {
	lag := headRevision - atRevision
	if lag < 0 {
		lag = 0
	}
	return lag <= p.Threshold
}

// Lag computes revision distance between head and token revision.
func (p *SnapshotPolicy) Lag(st *store.Store, atRevision int64) (int64, error) {
	head, err := st.CurrentRevision()
	if err != nil {
		return 0, err
	}
	lag := head - atRevision
	if lag < 0 {
		lag = 0
	}
	return lag, nil
}
