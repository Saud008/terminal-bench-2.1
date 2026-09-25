package atlasseal

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/airclos/internal/labtypes"
)

const (
	defaultOut  = "/app/output/impact-closure-atlas.json"
	epochPath   = "/app/state/seal-epoch.json"
	latticePath = "/app/state/closure-lattice.json"
)

func Publish(scenario, outPath string) error {
	var ep labtypes.SealEpoch
	raw, err := os.ReadFile(epochPath)
	if err != nil {
		return fmt.Errorf("seal_epoch missing")
	}
	if err := json.Unmarshal(raw, &ep); err != nil {
		return err
	}
	if ep.SealEpoch <= 0 {
		return fmt.Errorf("seal blocked: seal_epoch must be > 0")
	}
	latticeRaw, err := os.ReadFile(latticePath)
	if err != nil {
		return err
	}
	var lattice labtypes.ClosureLattice
	if err := json.Unmarshal(latticeRaw, &lattice); err != nil {
		return err
	}
	closures := lattice.RouteClosures
	sort.Slice(closures, func(i, j int) bool {
		if closures[i].FlightID != closures[j].FlightID {
			return closures[i].FlightID > closures[j].FlightID
		}
		return closures[i].NotamID > closures[j].NotamID
	})
	atlas := labtypes.ImpactClosureAtlas{
		Scenario:         scenario,
		EvalMinute:       lattice.EvalMinute,
		ActiveNotamCount: lattice.ActiveNotamCount,
		SealedSectors:    lattice.SealedSectors,
		RouteClosures:    closures,
	}
	digest, err := atlasDigest(atlas)
	if err != nil {
		return err
	}
	atlas.AtlasDigest = digest
	if outPath == "" {
		outPath = defaultOut
	}
	return writeAtlas(outPath, atlas)
}

func atlasDigest(atlas labtypes.ImpactClosureAtlas) (string, error) {
	payload := map[string]any{
		"active_notam_count": atlas.ActiveNotamCount,
		"sealed_sectors":     atlas.SealedSectors,
		"eval_minute":        atlas.EvalMinute,
		"route_closures":     atlas.RouteClosures,
		"scenario":           atlas.Scenario,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}

func writeAtlas(path string, atlas labtypes.ImpactClosureAtlas) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(atlas, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}
