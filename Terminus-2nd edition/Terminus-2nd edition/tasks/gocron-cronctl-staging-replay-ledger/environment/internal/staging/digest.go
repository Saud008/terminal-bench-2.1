package staging

import (
	"fmt"
	"sort"

	"github.com/terminus/gocron-overlap-repair/internal/model"
)

// ComputeFiresDigest returns the stable hex digest for planned fire rows.
func ComputeFiresDigest(fires []model.PlannedFire) string {
	sorted := append([]model.PlannedFire(nil), fires...)
	sort.Slice(sorted, func(i, j int) bool {
		if sorted[i].AtMs == sorted[j].AtMs {
			return sorted[i].JobID < sorted[j].JobID
		}
		return sorted[i].AtMs < sorted[j].AtMs
	})
	var payload []byte
	for _, f := range sorted {
		payload = append(payload, []byte(fmt.Sprintf("%s:%d\n", f.JobID, f.AtMs))...)
	}
	return fmt.Sprintf("%016x", fnv1a64(payload))
}

func fnv1a64(data []byte) uint64 {
	const (
		offset64 = 1469598103934665603
		prime64  = 1099511628211
	)
	h := uint64(offset64)
	for _, b := range data {
		h ^= uint64(b)
		h *= prime64
	}
	return h
}
