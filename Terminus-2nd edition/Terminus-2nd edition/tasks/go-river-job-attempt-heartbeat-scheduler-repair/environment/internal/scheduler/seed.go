package scheduler

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"strconv"

	"github.com/terminus/riverbench/internal/model"
	"github.com/terminus/riverbench/internal/store"
)

func LoadCatalog(path string) ([]model.SeedJob, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var jobs []model.SeedJob
	if err := json.Unmarshal(raw, &jobs); err != nil {
		return nil, err
	}
	return jobs, nil
}

func BuildProceduralJobs(seed string, catalog []model.SeedJob, defaultMax int, nowMs int64) []model.Job {
	offset := proceduralOffset(seed)
	out := make([]model.Job, 0, len(catalog))
	for i, spec := range catalog {
		id := spec.ID
		if id == "" {
			id = fmt.Sprintf("%s-%02d", spec.Kind, i+1)
		}
		priority := spec.Priority + (offset % 7)
		payload := fmt.Sprintf("%s:%s:%d", spec.Payload, seed, offset+i)
		maxAttempts := spec.MaxAttempts
		if maxAttempts <= 0 {
			maxAttempts = defaultMax
		}
		out = append(out, model.Job{
			ID:          id,
			Kind:        spec.Kind,
			Payload:     payload,
			Priority:    priority,
			State:       model.StatePending,
			Attempts:    0,
			MaxAttempts: maxAttempts,
			AvailableAt: nowMs,
			CreatedAt:   nowMs,
		})
	}
	return out
}

func proceduralOffset(seed string) int {
	sum := sha256.Sum256([]byte(seed))
	return int(hexToInt(sum[:4]) % 997)
}

func hexToInt(b []byte) int64 {
	return int64(int(b[0])<<24 | int(b[1])<<16 | int(b[2])<<8 | int(b[3]))
}

func SeedStore(st *store.Store, req model.SeedRequest, catalogPath string, defaultMax int, nowMs int64) (int, error) {
	if err := st.Reset(); err != nil {
		return 0, err
	}
	var specs []model.SeedJob
	if len(req.Jobs) > 0 {
		specs = req.Jobs
	} else {
		var err error
		specs, err = LoadCatalog(catalogPath)
		if err != nil {
			return 0, err
		}
	}
	jobs := BuildProceduralJobs(req.Seed, specs, defaultMax, nowMs)
	for _, job := range jobs {
		if err := st.InsertJob(job); err != nil {
			return 0, err
		}
	}
	return len(jobs), nil
}

func ParseInjectExpiry(raw string, nowMs int64) (int64, error) {
	if raw == "" {
		return nowMs - 1, nil
	}
	v, err := strconv.ParseInt(raw, 10, 64)
	if err != nil {
		return 0, err
	}
	return v, nil
}
