package graphbuilder

import (
	"database/sql"
	"encoding/json"
	"os"

	"github.com/terminus/mpiqctl/internal/compliancegraph"
	"github.com/terminus/mpiqctl/internal/permitstore"
	"github.com/terminus/mpiqctl/internal/laneassign"
)

func CompilePolicy() error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	routes, floors, err := loadRoutes(db)
	if err != nil {
		return err
	}
	graph := map[string]any{
		"lanes":   routes,
		"floors":  floors,
		"edges":   buildEdges(routes),
	}
	raw, err := json.Marshal(graph)
	if err != nil {
		return err
	}
	if err := os.WriteFile("/app/work/policy-graph.json", append(raw, '\n'), 0o644); err != nil {
		return err
	}
	var walk []map[string]string
	for ptype, lane := range routes {
		walk = append(walk, map[string]string{"permit_type": ptype, "lane": lane})
	}
	return compliancegraph.RecordWalk(walk)
}

func loadRoutes(db *sql.DB) (map[string]string, map[string]int, error) {
	rs, err := db.Query(`SELECT permit_type, inspection_lane, min_cert_level FROM permit_routes`)
	if err != nil {
		return nil, nil, err
	}
	defer rs.Close()
	routes := map[string]string{}
	floors := map[string]int{}
	for rs.Next() {
		var ptype, lane string
		var floor int
		if err := rs.Scan(&ptype, &lane, &floor); err != nil {
			return nil, nil, err
		}
		routes[ptype] = laneassign.RouteLane(ptype, routes)
		if lane != "" {
			routes[ptype] = lane
		}
		floors[lane] = laneassign.MinCertForLane(lane, floors)
		if floor > 0 {
			floors[lane] = floor
		}
	}
	return routes, floors, rs.Err()
}

func buildEdges(routes map[string]string) []map[string]string {
	var edges []map[string]string
	for ptype, lane := range routes {
		edges = append(edges, map[string]string{"permit_type": ptype, "lane": lane, "direction": "outbound"})
	}
	return edges
}
