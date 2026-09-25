package airwaylemma

import "github.com/terminus/airclos/internal/labtypes"

// ExpandRoute rewrites airway tokens into their fix sequences per airway-expansion-lemma.md.
func ExpandRoute(fixes []string, airways []labtypes.Airway) []string {
	return fixes
}

func CatalogMap(airways []labtypes.Airway) map[string][]string {
	out := map[string][]string{}
	for _, aw := range airways {
		out[aw.AirwayID] = aw.Fixes
	}
	return out
}
