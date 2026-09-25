package authzkernel

import "github.com/terminus/casctl/internal/model"

func KeyMatch(obj, pattern string) bool {
	if pattern == "*" {
		return true
	}
	return obj == pattern
}

func MatchRequest(req model.Request, pol model.Policy, gs []model.Grouping) bool {
	if req.Dom != pol.Dom {
		return false
	}
	if !HasRole(req.Sub, pol.Sub, req.Dom, gs) {
		return false
	}
	if !KeyMatch(req.Obj, pol.Obj) {
		return false
	}
	return KeyMatch(req.Act, pol.Act)
}
