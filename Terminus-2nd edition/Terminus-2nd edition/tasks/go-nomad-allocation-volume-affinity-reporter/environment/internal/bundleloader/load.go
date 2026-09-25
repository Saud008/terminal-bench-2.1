package bundleloader

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
)

func ScenarioPath(dir, name string) string {
	if filepath.Ext(name) != ".json" {
		name = name + ".json"
	}
	return filepath.Join(dir, name)
}

func ScopeAllocID(seed, allocID string) string {
	x := uint32(2166136261)
	for _, b := range []byte(seed + ":" + allocID) {
		x ^= uint32(b)
		x *= 16777619
	}
	return fmt.Sprintf("%s-%08x", allocID, x)
}

func LoadScenario(path, seed string) (model.ScenarioFile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.ScenarioFile{}, err
	}
	var sc model.ScenarioFile
	if err := json.Unmarshal(raw, &sc); err != nil {
		return model.ScenarioFile{}, err
	}
	return sc, nil
}

func Materialize(sc model.ScenarioFile, seed string) []model.ScopedAllocation {
	out := make([]model.ScopedAllocation, 0, len(sc.Allocations))
	for _, a := range sc.Allocations {
		out = append(out, model.ScopedAllocation{
			AllocID:            ScopeAllocID(seed, a.AllocID),
			JobID:              sc.JobID,
			TaskGroup:          sc.TaskGroup,
			NodeID:             a.NodeID,
			NodeClass:          a.NodeClass,
			CreateIndex:        a.CreateIndex,
			ModifyIndex:        a.ModifyIndex,
			ClientStatus:       a.ClientStatus,
			DesiredStatus:      a.DesiredStatus,
			RescheduleAttempts: a.RescheduleAttempts,
			RescheduleFailed:   a.RescheduleFailed,
			CSIMounts:          append([]model.CSIMount(nil), a.CSIMounts...),
			Constraints:        append([]model.Constraint(nil), a.Constraints...),
			Affinities:         append([]model.Affinity(nil), a.Affinities...),
			SupersededBy:       a.SupersededBy,
		})
	}
	return out
}

func FindAlloc(allocs []model.ScopedAllocation, id string) (model.ScopedAllocation, bool) {
	for _, a := range allocs {
		if a.AllocID == id {
			return a, true
		}
	}
	return model.ScopedAllocation{}, false
}
