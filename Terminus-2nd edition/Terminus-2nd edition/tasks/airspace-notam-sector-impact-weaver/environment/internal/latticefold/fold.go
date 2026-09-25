package latticefold

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

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
					if runwaylemma.RunwayMatch(rw, n.Runway) && flight.Airport == n.Airport {
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
	data, err := json.MarshalIndent(ep, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(epochPath, data, 0o644)
}
