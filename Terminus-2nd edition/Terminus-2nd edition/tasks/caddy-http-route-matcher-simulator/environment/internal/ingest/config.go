package ingest

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/caddyroute/internal/types"
)

// LoadRouteFile reads a Caddy-style routes JSON document.
func LoadRouteFile(path string) (*types.RouteFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var rf types.RouteFile
	if err := json.Unmarshal(data, &rf); err != nil {
		return nil, fmt.Errorf("decode routes: %w", err)
	}
	return &rf, nil
}
