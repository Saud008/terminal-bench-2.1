package authzkernel

import "github.com/terminus/casctl/internal/model"

func HasRole(sub, role, dom string, gs []model.Grouping) bool {
	if sub == role {
		return true
	}
	seen := map[string]bool{}
	queue := []string{sub}
	for len(queue) > 0 {
		cur := queue[0]
		queue = queue[1:]
		if cur == role {
			return true
		}
		if seen[cur] {
			continue
		}
		seen[cur] = true
		for _, g := range gs {
			if g.Dom == dom && g.Child == cur && !seen[g.Parent] {
				queue = append(queue, g.Parent)
			}
		}
	}
	return false
}
