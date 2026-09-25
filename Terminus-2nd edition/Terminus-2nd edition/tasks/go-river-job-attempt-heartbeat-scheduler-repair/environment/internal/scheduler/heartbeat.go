package scheduler

import (
	"fmt"

	"github.com/terminus/riverbench/internal/model"
	"github.com/terminus/riverbench/internal/store"
)

// ExtendHeartbeat refreshes lease expiry for a claimed job.
func ExtendHeartbeat(st *store.Store, workerID, jobID string, nowMs, leaseMs int64) (model.Lease, error) {
	lease, err := st.GetLatestLeaseForWorker(workerID)
	if err != nil {
		return model.Lease{}, fmt.Errorf("heartbeat: %w", err)
	}
	lease.ExpiresAtMs = nowMs + leaseMs
	lease.HeartbeatMs = nowMs
	if err := st.UpsertLease(lease); err != nil {
		return model.Lease{}, err
	}
	return lease, nil
}
