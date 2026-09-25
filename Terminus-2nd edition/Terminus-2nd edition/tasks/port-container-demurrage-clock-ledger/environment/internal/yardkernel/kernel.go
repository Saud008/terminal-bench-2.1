package yardkernel

import (
	"crypto/sha256"
	"encoding/hex"

	"github.com/terminus/demurctl/internal/model"
)

func remapID(seed, original string) string {
	sum := sha256.Sum256([]byte(seed + ":" + original))
	return "CNT-" + hex.EncodeToString(sum[:4])
}

// RemapScenario rewrites container identifiers when DEMUR_SEED is set.
func RemapScenario(sc model.Scenario, seed string) model.Scenario {
	idMap := map[string]string{}
	for _, c := range sc.Containers {
		idMap[c.ContainerID] = remapID(seed, c.ContainerID)
	}
	for i, c := range sc.Containers {
		sc.Containers[i].ContainerID = idMap[c.ContainerID]
	}
	for i, e := range sc.GateEvents {
		sc.GateEvents[i].ContainerID = idMap[e.ContainerID]
	}
	for i, c := range sc.Contracts {
		sc.Contracts[i].ContainerID = idMap[c.ContainerID]
	}
	for i, h := range sc.Holds {
		sc.Holds[i].ContainerID = idMap[h.ContainerID]
	}
	return sc
}

// ValidateKernel reports whether yard compliance kernel accepts scenario shape.
func ValidateKernel(sc model.Scenario) bool {
	return sc.ScenarioID != "" && len(sc.Containers) > 0
}
