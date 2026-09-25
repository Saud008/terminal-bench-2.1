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
			if i >= len(dsNames) {
				break
			}
			kind := typesDB[typeName][dsNames[i]]
			out = append(out, model.NormalizedPoint{
				CanonicalID: canon,
				DS:          dsNames[i],
				ValueKind:   exportKind(kind),
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

func exportKind(kind string) string {
	switch kind {
	case "derive":
		return "derive_rate"
	case "counter":
		return "counter_delta"
	case "absolute":
		return "absolute"
	default:
		return "gauge"
	}
}

func PairRates(points []model.NormalizedPoint, kind string) []model.NormalizedPoint {
	if len(points) < 2 || (kind != "derive" && kind != "counter") {
		return points
	}
	ordered := append([]model.NormalizedPoint(nil), points...)
	sort.Slice(ordered, func(i, j int) bool { return ordered[i].Epoch < ordered[j].Epoch })
	p1 := ordered[len(ordered)-2]
	p2 := ordered[len(ordered)-1]
	dt := float64(p2.Epoch - p1.Epoch)
	if dt <= 0 {
		return points
	}
	delta := p2.Value - p1.Value
	if kind == "counter" {
		if delta < 0 {
			delta = float64(uint64(1<<32)) - p1.Value + p2.Value
		}
		return []model.NormalizedPoint{{
			CanonicalID: p2.CanonicalID,
			DS:          p2.DS,
			ValueKind:   "counter_delta",
			Epoch:       p2.Epoch,
			Value:       delta,
		}}
	}
	if delta < 0 {
		delta += float64(uint64(1 << 32))
	}
	return []model.NormalizedPoint{{
		CanonicalID: p2.CanonicalID,
		DS:          p2.DS,
		ValueKind:   "derive_rate",
		Epoch:       p2.Epoch,
		Value:       delta / dt,
	}}
}
