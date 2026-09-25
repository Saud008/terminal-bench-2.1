package ingest

import "github.com/terminus/ballotmesh/internal/model"

func Normalize(m model.Mesh) model.Mesh {
	if m.DefaultTTLMS <= 0 {
		m.DefaultTTLMS = 30000
	}
	if m.Topology.Kind == "" {
		m.Topology.Kind = "star"
	}
	return m
}
