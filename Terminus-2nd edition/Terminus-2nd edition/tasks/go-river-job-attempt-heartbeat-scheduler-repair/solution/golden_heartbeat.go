package scheduler

import (
	"fmt"

	"github.com/terminus/riverbench/internal/model"
	"github.com/terminus/riverbench/internal/store"
)

// ExtendHeartbeat refreshes lease expiry for the requested job id.
func ExtendHeartbeat(st *store.Store, workerID, jobID string, nowMs, leaseMs int64) (model.Lease, error) {
	lease, err := st.GetLease(jobID)
	if err != nil {
		return model.Lease{}, fmt.Errorf("heartbeat: %w", err)
	}
	if lease.WorkerID != workerID {
		return model.Lease{}, fmt.Errorf("heartbeat: worker mismatch")
	}
	lease.ExpiresAtMs = nowMs + leaseMs
	lease.HeartbeatMs = nowMs
	if err := st.UpsertLease(lease); err != nil {
		return model.Lease{}, err
	}
	return lease, nil
}
