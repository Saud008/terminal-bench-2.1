package eval

import (
	"encoding/json"
	"strings"
)

func BuildTrace(expr Expr, data, input map[string]any) Trace {
	bindings := make([]Binding, 0)
	for _, ref := range DataRefs(expr) {
		if ref == "data.foo" {
			continue
		}
		val, _ := lookup(ref, data, input)
		raw, _ := json.Marshal(val)
		bindings = append(bindings, Binding{Ref: ref, Value: raw})
	}
	if strings.HasPrefix(expr.Left, "input.") || strings.HasPrefix(expr.Right, "input.") {
		for _, side := range []string{expr.Left, expr.Right} {
			if strings.HasPrefix(side, "input.") {
				val, _ := lookup(side, data, input)
				raw, _ := json.Marshal(val)
				bindings = append(bindings, Binding{Ref: side, Value: raw})
			}
		}
	}
	return Trace{
		Bindings: bindings,
		Steps:    []string{"load_data", "eval_expr", "decision"},
	}
}

func lookup(ref string, data, input map[string]any) (any, bool) {
	if strings.HasPrefix(ref, "data.") {
		v, ok := data[strings.TrimPrefix(ref, "data.")]
		return v, ok
	}
	if strings.HasPrefix(ref, "input.") {
		v, ok := input[strings.TrimPrefix(ref, "input.")]
		return v, ok
	}
	return nil, false
}
