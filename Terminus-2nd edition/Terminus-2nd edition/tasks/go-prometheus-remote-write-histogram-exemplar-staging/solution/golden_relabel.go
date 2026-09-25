package relabel

import "promingest/internal/model"

func DedupLabels(pairs []model.LabelPair) map[string]string {
	out := map[string]string{}
	for _, lp := range pairs {
		if _, exists := out[lp.Name]; exists {
			continue
		}
		out[lp.Name] = lp.Value
	}
	return out
}

func ApplySeries(series *model.Series) {
	labels := DedupLabels(series.Labels)
	ordered := make([]model.LabelPair, 0, len(labels))
	seen := map[string]struct{}{}
	for _, lp := range series.Labels {
		if _, ok := seen[lp.Name]; ok {
			continue
		}
		seen[lp.Name] = struct{}{}
		ordered = append(ordered, model.LabelPair{Name: lp.Name, Value: labels[lp.Name]})
	}
	series.Labels = ordered
}
