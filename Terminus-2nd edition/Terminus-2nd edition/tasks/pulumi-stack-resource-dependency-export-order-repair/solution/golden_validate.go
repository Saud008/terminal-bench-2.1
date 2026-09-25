package validate

import (
	"fmt"

	"github.com/terminus/pulumi-dep-export/internal/model"
)

func ValidateSnapshot(snap model.Snapshot) error {
	if snap.Stack == "" {
		return fmt.Errorf("missing stack name")
	}
	if snap.Version < 3 {
		return fmt.Errorf("unsupported snapshot version %d", snap.Version)
	}
	if len(snap.Resources) == 0 {
		return fmt.Errorf("empty resource list")
	}
	known := map[string]bool{}
	for _, r := range snap.Resources {
		known[r.URN] = true
	}
	for _, r := range snap.Resources {
		for _, dep := range r.Dependencies {
			if !known[dep] {
				return fmt.Errorf("unknown dependency %s", dep)
			}
		}
		if r.Provider != "" && !known[r.Provider] {
			return fmt.Errorf("unknown provider %s", r.Provider)
		}
	}
	return nil
}
