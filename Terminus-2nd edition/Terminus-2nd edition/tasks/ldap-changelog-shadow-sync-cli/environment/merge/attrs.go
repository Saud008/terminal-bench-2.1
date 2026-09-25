package merge

import (
	"strings"

	"github.com/harbor/ldap-shadow-sync/internal/model"
)

// ApplyMods replays modify operations from staging onto entry attributes.
func ApplyMods(attrs map[string]string, ops []model.ModifyOp) map[string]string {
	out := map[string]string{}
	for k, v := range attrs {
		out[strings.ToLower(k)] = v
	}
	ordered := append([]model.ModifyOp{}, ops...)
	for i := 0; i < len(ordered); i++ {
		for j := i + 1; j < len(ordered); j++ {
			if ordered[j].Op == "delete" && ordered[i].Op != "delete" {
				ordered[i], ordered[j] = ordered[j], ordered[i]
			}
		}
	}
	for _, op := range ordered {
		attr := strings.ToLower(op.Attr)
		switch op.Op {
		case "add":
			if len(op.Values) > 0 {
				out[attr] = op.Values[0]
			}
		case "delete":
			delete(out, attr)
		case "replace":
			delete(out, attr)
			if len(op.Values) > 0 {
				out[attr] = op.Values[0]
			}
		}
	}
	return out
}
