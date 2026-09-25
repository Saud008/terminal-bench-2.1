package packload

import (
	"fmt"
	"path/filepath"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/manifestio"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func BundlePath(dir, name string) string {
	return filepath.Join(dir, name+".json")
}

func LoadBundle(dir, name, seed string) (model.ManifestBundle, error) {
	_ = seed
	return manifestio.ReadBundle(BundlePath(dir, name))
}

func ScopeID(seed, id string) string {
	x := uint32(2166136261)
	for _, b := range []byte(seed + ":" + id) {
		x ^= uint32(b)
		x *= 16777619
	}
	return fmt.Sprintf("%s-%08x", id, x)
}

func Materialize(pack model.ManifestBundle, seed string) model.ManifestBundle {
	out := pack
	out.Models = make([]model.ModelNode, 0, len(pack.Models))
	for _, m := range pack.Models {
		deps := make([]string, 0, len(m.DependsOn))
		for _, d := range m.DependsOn {
			deps = append(deps, ScopeID(seed, d))
		}
		out.Models = append(out.Models, model.ModelNode{
			UniqueID:    ScopeID(seed, m.UniqueID),
			DependsOn:   deps,
			Enabled:     m.Enabled,
			LastBuiltAt: m.LastBuiltAt,
		})
	}
	out.Sources = make([]model.SourceNode, 0, len(pack.Sources))
	for _, s := range pack.Sources {
		out.Sources = append(out.Sources, model.SourceNode{
			UniqueID:          ScopeID(seed, s.UniqueID),
			LoadedAt:          s.LoadedAt,
			WarnAfterMinutes:  s.WarnAfterMinutes,
			ErrorAfterMinutes: s.ErrorAfterMinutes,
		})
	}
	out.Exposures = make([]model.ExposureNode, 0, len(pack.Exposures))
	for _, e := range pack.Exposures {
		deps := make([]string, 0, len(e.DependsOn))
		for _, d := range e.DependsOn {
			deps = append(deps, ScopeID(seed, d))
		}
		out.Exposures = append(out.Exposures, model.ExposureNode{
			UniqueID:  ScopeID(seed, e.UniqueID),
			DependsOn: deps,
		})
	}
	return out
}
