package lineage

import "github.com/terminus/mlflow-provenance-curator/internal/model"

func runByID(runs []model.ScopedRun, id string) (model.ScopedRun, bool) {
	for _, r := range runs {
		if r.RunID == id {
			return r, true
		}
	}
	return model.ScopedRun{}, false
}

// Closure walks parent_run_id from focus to root, root-first order.
func Closure(runs []model.ScopedRun, focus string) []string {
	chain := []string{}
	cur := focus
	seen := map[string]bool{}
	for cur != "" && !seen[cur] {
		seen[cur] = true
		chain = append(chain, cur)
		r, ok := runByID(runs, cur)
		if !ok || r.ParentRunID == "" {
			break
		}
		cur = r.ParentRunID
	}
	for i, j := 0, len(chain)-1; i < j; i, j = i+1, j-1 {
		chain[i], chain[j] = chain[j], chain[i]
	}
	return chain
}
