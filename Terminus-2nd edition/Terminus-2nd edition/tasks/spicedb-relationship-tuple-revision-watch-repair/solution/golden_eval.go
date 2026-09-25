package caveat

import (
	"encoding/json"
	"strings"

	"github.com/example/spicedb-relation-watch/internal/model"
)

// Evaluator applies caveat expressions on tuples.
type Evaluator struct{}

// New creates a caveat evaluator.
func New() *Evaluator {
	return &Evaluator{}
}

// Passes returns true when caveat allows subject at revision.
func (e *Evaluator) Passes(t *model.Tuple, subject string, tombstoneAtRevision *int64, atRevision int64) bool {
	if t == nil {
		return false
	}
	if tombstoneAtRevision != nil && *tombstoneAtRevision <= atRevision {
		return false
	}
	if t.CaveatExpr != nil && strings.TrimSpace(*t.CaveatExpr) != "" {
		var expr model.CaveatExpr
		if err := json.Unmarshal([]byte(*t.CaveatExpr), &expr); err == nil {
			if expr.AllowSubject != "" && expr.AllowSubject != subject {
				return false
			}
		}
	}
	return true
}
