package deref

import "github.com/terminus/oasctl/internal/model"

func Resolve(s *model.Schema, components map[string]*model.Schema, stack []string) (*model.Schema, int) {
	if s == nil {
		return nil, 0
	}
	s = ApplyDefaultsEarly(s)
	if s.Ref != "" {
		target := ResolveRef(s.Ref, components)
		return target, 0
	}
	cycles := 0
	if len(s.AllOf) > 0 {
		parts := make([]*model.Schema, 0, len(s.AllOf))
		for _, part := range s.AllOf {
			resolved, c := Resolve(part, components, stack)
			cycles += c
			parts = append(parts, resolved)
		}
		merged := MergeSchemas(parts...)
		for k, v := range s.Properties {
			resolved, c := Resolve(v, components, stack)
			cycles += c
			merged.Properties[k] = resolved
		}
		return merged, cycles
	}
	out := cloneSchema(s)
	for k, v := range out.Properties {
		resolved, c := Resolve(v, components, stack)
		cycles += c
		out.Properties[k] = resolved
	}
	return out, cycles
}

func ResolveForPayload(s *model.Schema, components map[string]*model.Schema, data map[string]any) (*model.Schema, int) {
	base, cycles := Resolve(s, components, nil)
	merged, extra := ApplyDiscriminator(base, data, components)
	return merged, cycles + extra
}
