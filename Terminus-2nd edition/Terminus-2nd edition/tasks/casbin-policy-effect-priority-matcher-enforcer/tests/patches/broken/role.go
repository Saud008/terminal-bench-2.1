package authzkernel

import "github.com/terminus/casctl/internal/model"

func HasRole(sub, role, dom string, gs []model.Grouping) bool {
	if sub == role {
		return true
	}
	for _, g := range gs {
		if g.Dom == dom && g.Child == sub && g.Parent == role {
			return true
		}
	}
	return false
}
