package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"
)

const planPath = "/app/state/pushdown-plan.json"

func WritePlan(plan model.PushdownPlan) error {
	raw, err := json.MarshalIndent(plan, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(planPath, append(raw, '\n'), 0o644)
}
