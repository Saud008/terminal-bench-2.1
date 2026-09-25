#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

cat > /app/internal/buffer/write.go <<'ORACLE_EOF'
package buffer

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/bundleloader"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
)

func WriteSnapshot(path, seed, scenario string, sc model.ScenarioFile) error {
	prev := int64(0)
	if raw, err := os.ReadFile(path); err == nil {
		var old model.BufferSnapshot
		if json.Unmarshal(raw, &old) == nil {
			prev = old.LoadSeq
		}
	}
	focus := bundleloader.ScopeAllocID(seed, sc.FocusAllocID)
	snap := model.BufferSnapshot{
		LoadSeq:      prev + 1,
		Seed:         seed,
		Scenario:     scenario,
		FocusAllocID: focus,
		JobID:        sc.JobID,
		TaskGroup:    sc.TaskGroup,
		StaleCutoff:  sc.StaleCutoffIndex,
		CSIVolumes:   sc.CSIVolumes,
		Allocations:  bundleloader.Materialize(sc, seed),
	}
	return writeJSON(path, snap)
}

func ReadSnapshot(path string) (model.BufferSnapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.BufferSnapshot{}, err
	}
	var snap model.BufferSnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.BufferSnapshot{}, err
	}
	return snap, nil
}

func ValidateSeedScenario(snap model.BufferSnapshot, seed, scenario string) error {
	if snap.Seed != seed || snap.Scenario != scenario {
		return fmt.Errorf("buffer seed/scenario mismatch")
	}
	return nil
}

func writeJSON(path string, v any) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}
ORACLE_EOF

cat > /app/internal/drain/gate.go <<'ORACLE_EOF'
package drain

import "github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"

func FilterEligible(allocs []model.ScopedAllocation) ([]model.ScopedAllocation, int) {
	eligible := make([]model.ScopedAllocation, 0, len(allocs))
	excluded := 0
	for _, a := range allocs {
		if a.ClientStatus == "down" || a.DesiredStatus == "stop" {
			excluded++
			continue
		}
		eligible = append(eligible, a)
	}
	return eligible, excluded
}
ORACLE_EOF

cat > /app/internal/lifecycle/attempts.go <<'ORACLE_EOF'
package lifecycle

import "github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"

func RescheduleTotal(allocs []model.ScopedAllocation) int {
	total := 0
	for _, a := range allocs {
		if a.RescheduleFailed && a.RescheduleAttempts > 0 {
			total += a.RescheduleAttempts
		}
	}
	return total
}
ORACLE_EOF

cat > /app/internal/lifecycle/suppress.go <<'ORACLE_EOF'
package lifecycle

import "github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"

func FilterStale(allocs []model.ScopedAllocation, cutoff uint64) ([]model.ScopedAllocation, int) {
	active := make([]model.ScopedAllocation, 0, len(allocs))
	suppressed := 0
	for _, a := range allocs {
		if a.SupersededBy != "" {
			suppressed++
			continue
		}
		if a.ModifyIndex < cutoff {
			suppressed++
			continue
		}
		active = append(active, a)
	}
	return active, suppressed
}
ORACLE_EOF

cat > /app/internal/mountlink/correlate.go <<'ORACLE_EOF'
package mountlink

import (
	"os"
	"sort"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
)

func namespaceSalt() string {
	return os.Getenv("TB3_NAMESPACE_SALT")
}

func volumeKey(vol model.CSIVolume) string {
	key := vol.Namespace + "/" + vol.VolumeID
	if s := namespaceSalt(); s != "" {
		key = key + s
	}
	return key
}

func JoinMounts(allocs []model.ScopedAllocation, volumes []model.CSIVolume) []model.VolumeJoinRow {
	volByID := map[string]model.CSIVolume{}
	for _, v := range volumes {
		volByID[v.VolumeID] = v
	}
	rows := make([]model.VolumeJoinRow, 0)
	for _, a := range allocs {
		for _, m := range a.CSIMounts {
			vol, ok := volByID[m.VolumeID]
			key := m.VolumeID
			plugin := ""
			joinOK := false
			if ok {
				key = volumeKey(vol)
				plugin = vol.PluginID
				joinOK = true
			}
			rows = append(rows, model.VolumeJoinRow{
				AllocID:   a.AllocID,
				VolumeKey: key,
				PluginID:  plugin,
				MountPath: m.MountPath,
				ReadOnly:  m.ReadOnly,
				JoinOK:    joinOK,
			})
		}
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].AllocID != rows[j].AllocID {
			return rows[i].AllocID < rows[j].AllocID
		}
		return rows[i].VolumeKey < rows[j].VolumeKey
	})
	return rows
}
ORACLE_EOF

cat > /app/internal/placement/lattice.go <<'ORACLE_EOF'
package placement

import (
	"sort"
	"strings"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/spread"
)

func nodeClassMatch(c model.Constraint, nodeClass string) bool {
	if c.Attribute != "${node.class}" {
		return true
	}
	switch c.Operator {
	case "=":
		return nodeClass == c.Value
	case "!=":
		return nodeClass != c.Value
	default:
		return false
	}
}

func affinityScore(a model.Affinity, nodePool string) int {
	if a.Attribute != "${node.pool}" {
		return 0
	}
	switch a.Operator {
	case "=":
		if nodePool == a.Value {
			return a.Weight
		}
	case "!=":
		if nodePool != a.Value {
			return a.Weight
		}
	}
	return 0
}

func RankPlacements(allocs []model.ScopedAllocation, nodePool string) []model.PlacementRow {
	type row struct {
		alloc model.ScopedAllocation
		score int
		hard  bool
	}
	passing := make([]row, 0, len(allocs))
	for _, a := range allocs {
		hardOK := true
		for _, c := range a.Constraints {
			if c.Hard && !nodeClassMatch(c, a.NodeClass) {
				hardOK = false
				break
			}
		}
		if !hardOK {
			continue
		}
		raw := 0
		for _, af := range a.Affinities {
			raw += affinityScore(af, nodePool)
		}
		score := spread.AdjustScore(raw, a, allocs)
		passing = append(passing, row{alloc: a, score: score, hard: hardOK})
	}
	sort.Slice(passing, func(i, j int) bool {
		if passing[i].score != passing[j].score {
			return passing[i].score > passing[j].score
		}
		return passing[i].alloc.AllocID < passing[j].alloc.AllocID
	})
	out := make([]model.PlacementRow, 0, len(passing))
	for i, p := range passing {
		out = append(out, model.PlacementRow{
			AllocID:       p.alloc.AllocID,
			NodeClass:     p.alloc.NodeClass,
			ConstraintOK:  p.hard,
			AffinityScore: p.score,
			PlacementRank: i + 1,
		})
	}
	return out
}

func ConstraintPass(allocs []model.ScopedAllocation) bool {
	for _, a := range allocs {
		for _, c := range a.Constraints {
			if c.Hard && strings.Contains(c.Attribute, "node.class") && !nodeClassMatch(c, a.NodeClass) {
				return false
			}
		}
	}
	return true
}
ORACLE_EOF

cat > /app/internal/spread/topology.go <<'ORACLE_EOF'
package spread

import "github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"

const penaltyWeight = 10

func PenaltyFor(a model.ScopedAllocation, peers []model.ScopedAllocation) int {
	count := 0
	for _, o := range peers {
		if o.NodeID == a.NodeID && o.AllocID != a.AllocID {
			count++
		}
	}
	return count * penaltyWeight
}

func PenaltyTotal(allocs []model.ScopedAllocation) int {
	total := 0
	for _, a := range allocs {
		total += PenaltyFor(a, allocs)
	}
	return total
}

func AdjustScore(base int, a model.ScopedAllocation, peers []model.ScopedAllocation) int {
	return base - PenaltyFor(a, peers)
}
ORACLE_EOF

go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/nomrep ./cmd/nomrep
bash /app/scripts/reset-state.sh
test -x /usr/local/bin/nomrep
