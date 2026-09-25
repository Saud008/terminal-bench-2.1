package authzkernel

import "github.com/terminus/casctl/internal/model"

func Decide(matches []model.Policy) string {
	hasAllow := false
	for _, m := range matches {
		if m.Eft == "deny" {
			return "deny"
		}
		if m.Eft == "allow" {
			hasAllow = true
		}
	}
	if hasAllow {
		return "allow"
	}
	return "deny"
}
