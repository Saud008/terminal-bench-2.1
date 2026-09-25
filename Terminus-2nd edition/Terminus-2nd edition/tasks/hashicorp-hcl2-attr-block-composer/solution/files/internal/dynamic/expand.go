package dynamic

import (
	"strings"

	"github.com/terminus/hclmerge/internal/types"
)

// ExpandAll expands dynamic blocks on a merged block.
func ExpandAll(block types.MergedBlock, fragments []types.Fragment) []map[string]interface{} {
	expanded := make([]map[string]interface{}, 0)
	flat := flattenAttrs(block.Attributes, "")
	for _, fr := range fragments {
		for _, dyn := range fr.Dynamics {
			for _, val := range dyn.Values {
				row := map[string]interface{}{"dynamic": dyn.Name}
				for k, tmpl := range dyn.Template {
					row[k] = strings.ReplaceAll(tmpl, "${value}", val)
				}
				for fk, fv := range flat {
					if strings.HasPrefix(fk, "tags.") {
						row[fk] = fv
					}
				}
				expanded = append(expanded, row)
			}
		}
	}
	return expanded
}

func flattenAttrs(attrs map[string]interface{}, prefix string) map[string]interface{} {
	out := map[string]interface{}{}
	for k, v := range attrs {
		full := k
		if prefix != "" {
			full = prefix + "." + k
		}
		if child, ok := v.(map[string]interface{}); ok {
			for dk, dv := range flattenAttrs(child, full) {
				out[dk] = dv
			}
			continue
		}
		out[full] = v
	}
	return out
}
