package ledger

import "github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"

// WrapPlan decorates a pushdown plan with optional ledger metadata.
func WrapPlan(plan model.PushdownPlan) model.PushdownPlan {
	plan.PlanWritten = plan.PlanWritten || len(plan.SelectedGroups) > 0
	return plan
}
