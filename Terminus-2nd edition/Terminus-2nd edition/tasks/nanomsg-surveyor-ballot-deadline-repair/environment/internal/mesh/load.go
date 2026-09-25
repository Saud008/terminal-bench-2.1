package mesh

import (
	"encoding/json"
	"os"

	"github.com/terminus/ballotmesh/internal/model"
)

func Load(path string) (model.Mesh, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Mesh{}, err
	}
	var m model.Mesh
	if err := json.Unmarshal(raw, &m); err != nil {
		return model.Mesh{}, err
	}
	return m, nil
}
