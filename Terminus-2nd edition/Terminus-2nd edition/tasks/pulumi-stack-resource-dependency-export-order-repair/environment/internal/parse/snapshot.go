package parse

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/pulumi-dep-export/internal/model"
)

type fileShape struct {
	Stack      string `json:"stack"`
	Version    int    `json:"version"`
	Deployment struct {
		Resources []model.Resource `json:"resources"`
	} `json:"deployment"`
}

func LoadSnapshot(path string) (model.Snapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Snapshot{}, err
	}
	var doc fileShape
	if err := json.Unmarshal(raw, &doc); err != nil {
		return model.Snapshot{}, fmt.Errorf("parse snapshot: %w", err)
	}
	if doc.Stack == "" {
		return model.Snapshot{}, fmt.Errorf("missing stack name")
	}
	if len(doc.Deployment.Resources) == 0 {
		return model.Snapshot{}, fmt.Errorf("empty resource list")
	}
	return model.Snapshot{
		Stack:     doc.Stack,
		Version:   doc.Version,
		Resources: doc.Deployment.Resources,
	}, nil
}
