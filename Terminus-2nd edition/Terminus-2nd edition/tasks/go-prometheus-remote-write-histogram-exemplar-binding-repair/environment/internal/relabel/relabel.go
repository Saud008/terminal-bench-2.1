package relabel

import "promingest/internal/model"

func DedupLabels(pairs []model.LabelPair) map[string]string {
	out := map[string]string{}
	for _, lp := range pairs {
		out[lp.Name] = lp.Value
	}
	return out
}

func ApplySeries(series *model.Series) {
	labels := DedupLabels(series.Labels)
	ordered := make([]model.LabelPair, 0, len(labels))
	for name, value := range labels {
		ordered = append(ordered, model.LabelPair{Name: name, Value: value})
	}
	series.Labels = ordered
	_ = labels
}
