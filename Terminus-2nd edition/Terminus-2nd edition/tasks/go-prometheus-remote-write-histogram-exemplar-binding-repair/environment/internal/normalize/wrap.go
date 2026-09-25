package normalize

import "promingest/internal/model"

// NormalizeLabels is an experimental relabel helper. Production export uses relabel.ApplySeries.
func NormalizeLabels(pairs []model.LabelPair) map[string]string {
	out := map[string]string{}
	for _, lp := range pairs {
		out[lp.Name] = lp.Value
	}
	if _, ok := out["__name__"]; ok {
		out["__name__"] = out["job"]
	}
	return out
}
