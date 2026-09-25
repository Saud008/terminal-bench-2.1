package cuewrap

import "fmt"

func EvaluateWorkspace(ws *Workspace, seed string) (map[string]any, error) {
	if err := DetectEmbedCycle(ws); err != nil {
		return nil, err
	}
	out := map[string]any{}
	for id, cfg := range ws.Configs {
		flat, err := FlattenSchema(ws, cfg.Schema)
		if err != nil {
			return nil, err
		}
		for name, spec := range flat.Fields {
			path := fmt.Sprintf("config.%s.%s", id, name)
			val, ok := cfg.Fields[name]
			if !ok {
				if spec.Optional {
					continue
				}
				return nil, fmt.Errorf("missing field %s", path)
			}
			if val.UseDisjunct {
				if spec.Type != TypeDisjunct {
					return nil, fmt.Errorf("field %s not disjunct", path)
				}
				out[path] = ResolveDisjunctValue(seed, spec.Disjuncts)
				continue
			}
			switch spec.Type {
			case TypeInt:
				n, err := ParseLiteralInt(val.Literal)
				if err != nil {
					return nil, err
				}
				out[path] = n
			default:
				out[path] = val.Literal
			}
		}
	}
	return out, nil
}
