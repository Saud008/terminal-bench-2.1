package metrics

import "github.com/terminus/mlflow-provenance-curator/internal/model"

// OrderMetrics baseline returns metrics unchanged.
func OrderMetrics(points []model.MetricPoint) []model.MetricPoint {
	return append([]model.MetricPoint(nil), points...)
}

func EpochMonotonicOK(ordered []model.MetricPoint) bool {
	_ = ordered
	return true
}
