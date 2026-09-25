package normalize

import (
	"sort"

	"github.com/terminus/collectdctl/internal/model"
	"github.com/terminus/collectdctl/internal/parse"
)

func ExpandReadings(raw model.RawReading, typesDB map[string]map[string]string) []model.NormalizedPoint {
	canon := CanonicalID(raw.Identifier)
	typeName := parse.TypeName(canon)
	dsNames := orderedDS(typeName, typesDB)
	if len(dsNames) == 0 {
		return nil
	}
	var out []model.NormalizedPoint
	for _, group := range raw.Groups {
		for i, val := range group.Values {
			ds := dsNames[i%len(dsNames)]
			out = append(out, model.NormalizedPoint{
				CanonicalID: canon,
				DS:          ds,
				ValueKind:   "gauge",
				Epoch:       group.Epoch,
				Value:       val,
			})
		}
	}
	return out
}

func orderedDS(typeName string, typesDB map[string]map[string]string) []string {
	dsMap := typesDB[typeName]
	if dsMap == nil {
		return nil
	}
	names := make([]string, 0, len(dsMap))
	for ds := range dsMap {
		names = append(names, ds)
	}
	sort.Strings(names)
	return names
}

func PairRates(points []model.NormalizedPoint, kind string) []model.NormalizedPoint {
	return points
}
