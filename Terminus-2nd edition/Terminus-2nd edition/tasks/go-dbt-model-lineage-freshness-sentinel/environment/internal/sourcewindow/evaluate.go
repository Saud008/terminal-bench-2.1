package sourcewindow

import (
	"time"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func ParseRFC3339(s string) (time.Time, error) {
	return time.Parse(time.RFC3339, s)
}

func EvaluateSources(sources []model.SourceNode, evaluatedAt string) ([]model.FreshnessStatus, error) {
	eval, err := ParseRFC3339(evaluatedAt)
	if err != nil {
		return nil, err
	}
	out := make([]model.FreshnessStatus, 0, len(sources))
	for _, s := range sources {
		loaded, err := ParseRFC3339(s.LoadedAt)
		if err != nil {
			return nil, err
		}
		mins := int(eval.Sub(loaded).Minutes())
		status := "ok"
		if mins >= s.WarnAfterMinutes {
			status = "warn"
		}
		if mins >= s.ErrorAfterMinutes {
			status = "error"
		}
		out = append(out, model.FreshnessStatus{
			UniqueID: s.UniqueID,
			Minutes:  mins,
			Status:   status,
		})
	}
	return out, nil
}
