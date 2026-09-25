#!/usr/bin/env bash
set -euo pipefail

find /app/internal /app/cmd -name "*.go" -exec sed -i "s/\r$//" {} +

cat > /app/internal/amendlemma/amend.go <<'GOEOF'
package amendlemma

import "github.com/terminus/airclos/internal/labtypes"

// CloseSeries keeps the maximum amendment per series_id per amendment-closure-lemma.md.
func CloseSeries(notams []labtypes.NotamRecord) []labtypes.NotamRecord {
	best := map[string]labtypes.NotamRecord{}
	for _, n := range notams {
		cur, ok := best[n.SeriesID]
		if !ok || n.Amendment > cur.Amendment {
			best[n.SeriesID] = n
		}
	}
	out := make([]labtypes.NotamRecord, 0, len(best))
	for _, v := range best {
		out = append(out, v)
	}
	return out
}
GOEOF

cat > /app/internal/chronolemma/window.go <<'GOEOF'
package chronolemma

// ActiveAt reports activation over a wrapping minute axis per chronology-window-lemma.md.
func ActiveAt(startMinute, endMinute, evalMinute int) bool {
	if endMinute < startMinute {
		return evalMinute >= startMinute || evalMinute <= endMinute
	}
	return evalMinute >= startMinute && evalMinute <= endMinute
}
GOEOF

cat > /app/internal/runwaylemma/runway.go <<'GOEOF'
package runwaylemma

import (
	"regexp"
	"strings"
)

var runwayRe = regexp.MustCompile(`^0*(\d+)([LRC]?)$`)

// NormalizeRunway canonicalizes a runway designator per runway-normalization-lemma.md.
func NormalizeRunway(raw string) string {
	s := strings.ToUpper(strings.TrimSpace(raw))
	m := runwayRe.FindStringSubmatch(s)
	if m == nil {
		return s
	}
	return m[1] + m[2]
}

func RunwayMatch(a, b string) bool {
	return NormalizeRunway(a) == NormalizeRunway(b)
}
GOEOF

cat > /app/internal/airwaylemma/airway.go <<'GOEOF'
package airwaylemma

import "github.com/terminus/airclos/internal/labtypes"

// ExpandRoute rewrites airway tokens into their fix sequences per airway-expansion-lemma.md.
func ExpandRoute(fixes []string, airways []labtypes.Airway) []string {
	catalog := CatalogMap(airways)
	var out []string
	for _, token := range fixes {
		seq, ok := catalog[token]
		if !ok {
			if len(out) > 0 && out[len(out)-1] == token {
				continue
			}
			out = append(out, token)
			continue
		}
		if len(out) > 0 && len(seq) > 0 && out[len(out)-1] == seq[0] {
			seq = seq[1:]
		}
		out = append(out, seq...)
	}
	return out
}

func CatalogMap(airways []labtypes.Airway) map[string][]string {
	out := map[string][]string{}
	for _, aw := range airways {
		out[aw.AirwayID] = aw.Fixes
	}
	return out
}
GOEOF

cat > /app/internal/spatiallemma/spatial.go <<'GOEOF'
package spatiallemma

import "github.com/terminus/airclos/internal/labtypes"

func pointOnSegment(p labtypes.Point, a, b labtypes.Point) bool {
	cross := (p.Y-a.Y)*(b.X-a.X) - (p.X-a.X)*(b.Y-a.Y)
	if cross < -1e-9 || cross > 1e-9 {
		return false
	}
	dot := (p.X-a.X)*(p.X-b.X) + (p.Y-a.Y)*(p.Y-b.Y)
	return dot <= 1e-9
}

// PointInside runs an inclusive-boundary ray cast per sector-spatial-lemma.md.
func PointInside(p labtypes.Point, poly []labtypes.Point) bool {
	n := len(poly)
	if n < 3 {
		return false
	}
	inside := false
	j := n - 1
	for i := 0; i < n; i++ {
		xi, yi := poly[i].X, poly[i].Y
		xj, yj := poly[j].X, poly[j].Y
		if pointOnSegment(p, poly[i], poly[j]) {
			return true
		}
		intersect := (yi > p.Y) != (yj > p.Y) && p.X < (xj-xi)*(p.Y-yi)/(yj-yi+0.0)+xi
		if intersect {
			inside = !inside
		}
		j = i
	}
	return inside
}

func SectorForPoint(p labtypes.Point, sectors []labtypes.Sector) []string {
	var hits []string
	for _, s := range sectors {
		if PointInside(p, s.Polygon) {
			hits = append(hits, s.SectorID)
		}
	}
	return hits
}
GOEOF

cat > /app/internal/bindvault/vault.go <<'GOEOF'
package bindvault

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/airclos/internal/labtypes"
)

const DefaultBindingPath = "/app/state/campaign-binding.json"

func WriteBinding(path string, binding labtypes.CampaignBinding) error {
	if path == "" {
		path = DefaultBindingPath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	digest, err := computeDigest(binding.Scenario, binding.Notams, binding.Sectors, binding.Flights, binding.Airways, binding.FixPoints, binding.Policy)
	if err != nil {
		return err
	}
	binding.BindingDigest = digest
	data, err := json.MarshalIndent(binding, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func ReadBinding(path string) (labtypes.CampaignBinding, error) {
	if path == "" {
		path = DefaultBindingPath
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return labtypes.CampaignBinding{}, err
	}
	var binding labtypes.CampaignBinding
	if err := json.Unmarshal(raw, &binding); err != nil {
		return labtypes.CampaignBinding{}, err
	}
	return binding, nil
}

func computeDigest(scenario string, notams []labtypes.NotamRecord, sectors []labtypes.Sector, flights []labtypes.FlightPlan, airways []labtypes.Airway, fixPoints []labtypes.FixPoint, policy labtypes.Policy) (string, error) {
	payload := map[string]any{
		"policy":     policy,
		"scenario":   scenario,
		"notams":     notams,
		"sectors":    sectors,
		"flights":    flights,
		"airways":    airways,
		"fix_points": fixPoints,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}
GOEOF

cat > /app/internal/latticefold/fold.go <<'GOEOF'
package latticefold

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/terminus/airclos/internal/airwaylemma"
	"github.com/terminus/airclos/internal/bindvault"
	"github.com/terminus/airclos/internal/chronoclose"
	"github.com/terminus/airclos/internal/labtypes"
	"github.com/terminus/airclos/internal/runwaylemma"
	"github.com/terminus/airclos/internal/spatiallemma"
)

const (
	latticePath = "/app/state/closure-lattice.json"
	epochPath   = "/app/state/seal-epoch.json"
)

func Run(scenario string) error {
	active, err := chronoclose.ReadClosure("")
	if err != nil {
		return err
	}
	binding, err := bindvault.ReadBinding("")
	if err != nil {
		return err
	}
	lattice := BuildLattice(scenario, active, binding)
	if err := writeLattice(latticePath, lattice); err != nil {
		return err
	}
	return bumpEpoch()
}

func BuildLattice(scenario string, active labtypes.ChronologyClosure, binding labtypes.CampaignBinding) labtypes.ClosureLattice {
	sectorSet := map[string]struct{}{}
	closures := make([]labtypes.RouteClosure, 0)
	fixPoints := fixCoordinateMap(binding.FixPoints)

	for _, flight := range binding.Flights {
		expanded := airwaylemma.ExpandRoute(flight.RouteFixes, binding.Airways)
		for _, fix := range expanded {
			if pt, ok := fixPoints[fix]; ok {
				for _, sid := range spatiallemma.SectorForPoint(pt, binding.Sectors) {
					sectorSet[sid] = struct{}{}
				}
			}
		}
		for _, n := range active.ActiveNotams {
			switch n.Kind {
			case "sector":
				for _, fix := range expanded {
					if pt, ok := fixPoints[fix]; ok {
						if spatiallemma.PointInside(pt, n.Polygon) {
							sectorSet[n.SectorID] = struct{}{}
							closures = append(closures, labtypes.RouteClosure{
								FlightID:   flight.FlightID,
								ImpactCode: "sector_penetration",
								Detail:     n.SectorID,
								NotamID:    n.NotamID,
							})
						}
					}
				}
			case "runway":
				for _, rw := range flight.Runways {
					if runwaylemma.RunwayMatch(rw, n.Runway) && strings.EqualFold(strings.TrimSpace(flight.Airport), strings.TrimSpace(n.Airport)) {
						closures = append(closures, labtypes.RouteClosure{
							FlightID:   flight.FlightID,
							ImpactCode: "runway_closure",
							Detail:     n.Runway,
							NotamID:    n.NotamID,
						})
					}
				}
			case "route":
				for _, fix := range expanded {
					if fix == n.RouteFix || fix == n.AirwayID {
						closures = append(closures, labtypes.RouteClosure{
							FlightID:   flight.FlightID,
							ImpactCode: "route_restriction",
							Detail:     n.RouteFix,
							NotamID:    n.NotamID,
						})
					}
				}
			}
		}
	}

	sectors := make([]string, 0, len(sectorSet))
	for sid := range sectorSet {
		sectors = append(sectors, sid)
	}
	sort.Strings(sectors)
	sort.Slice(closures, func(i, j int) bool {
		if closures[i].FlightID != closures[j].FlightID {
			return closures[i].FlightID < closures[j].FlightID
		}
		return closures[i].NotamID < closures[j].NotamID
	})

	return labtypes.ClosureLattice{
		Scenario:         scenario,
		EvalMinute:       active.EvalMinute,
		SealedSectors:    sectors,
		RouteClosures:    closures,
		ActiveNotamCount: len(active.ActiveNotams),
	}
}

func fixCoordinateMap(fixes []labtypes.FixPoint) map[string]labtypes.Point {
	out := map[string]labtypes.Point{}
	for _, f := range fixes {
		out[f.FixID] = labtypes.Point{X: f.X, Y: f.Y}
	}
	return out
}

func writeLattice(path string, lattice labtypes.ClosureLattice) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(lattice, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func bumpEpoch() error {
	var ep labtypes.SealEpoch
	if raw, err := os.ReadFile(epochPath); err == nil {
		_ = json.Unmarshal(raw, &ep)
	}
	ep.SealEpoch = ep.SealEpoch + 1
	data, err := json.MarshalIndent(ep, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(epochPath, data, 0o644)
}
GOEOF

cat > /app/internal/atlasseal/seal.go <<'GOEOF'
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
	if closures == nil {
		closures = make([]labtypes.RouteClosure, 0)
	}
	sort.Slice(closures, func(i, j int) bool {
		if closures[i].FlightID != closures[j].FlightID {
			return closures[i].FlightID < closures[j].FlightID
		}
		return closures[i].NotamID < closures[j].NotamID
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
GOEOF

echo "airclos closure-lab oracle lemmas installed"
