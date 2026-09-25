// Domain-scoped request binding for access-decision policy rules.
package authzkernel

import "github.com/terminus/casctl/internal/model"

func KeyMatch(obj, pattern string) bool {
	if pattern == "*" {
		return true
	}
	return obj == pattern
}

func MatchRequest(req model.Request, pol model.Policy, gs []model.Grouping) bool {
	if !HasRole(req.Sub, pol.Sub, req.Dom, gs) {
		return false
	}
	if !KeyMatch(req.Act, pol.Obj) {
		return false
	}
	if req.Obj != pol.Act {
		return false
	}
	return true
}
