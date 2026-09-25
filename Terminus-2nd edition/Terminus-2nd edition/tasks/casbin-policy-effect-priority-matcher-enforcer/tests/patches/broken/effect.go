package authzkernel

import "github.com/terminus/casctl/internal/model"

func Decide(matches []model.Policy) string {
	if len(matches) == 0 {
		return "deny"
	}
	hasAllow := false
	for _, m := range matches {
		if m.Eft == "allow" {
			hasAllow = true
		}
	}
	if hasAllow {
		return "allow"
	}
	return "deny"
}
