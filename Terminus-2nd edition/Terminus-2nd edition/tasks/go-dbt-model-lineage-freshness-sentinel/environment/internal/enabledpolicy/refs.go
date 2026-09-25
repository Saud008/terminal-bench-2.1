package enabledpolicy

import (
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func EnabledReferencesDisabled(models []model.ModelNode) bool {
	enabled := map[string]bool{}
	for _, m := range models {
		if m.Enabled {
			enabled[m.UniqueID] = true
		}
	}
	for _, m := range models {
		if !m.Enabled {
			continue
		}
		for _, d := range m.DependsOn {
			if !enabled[d] {
				return false
			}
		}
	}
	return true
}
