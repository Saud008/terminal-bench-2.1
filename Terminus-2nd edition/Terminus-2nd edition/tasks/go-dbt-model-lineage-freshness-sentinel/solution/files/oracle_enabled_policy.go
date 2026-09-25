package enabledpolicy

import (
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func EnabledReferencesDisabled(models []model.ModelNode) bool {
	enabled := map[string]bool{}
	disabled := map[string]bool{}
	for _, m := range models {
		if m.Enabled {
			enabled[m.UniqueID] = true
		} else {
			disabled[m.UniqueID] = true
		}
	}
	for _, m := range models {
		if !m.Enabled {
			continue
		}
		for _, dep := range m.DependsOn {
			if disabled[dep] {
				return false
			}
			if len(dep) >= 6 && dep[:6] == "model." && !enabled[dep] {
				return false
			}
		}
	}
	return true
}
