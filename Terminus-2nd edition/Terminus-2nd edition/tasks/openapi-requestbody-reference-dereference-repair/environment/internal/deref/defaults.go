package deref

import "github.com/terminus/oasctl/internal/model"

func ApplyDefaultsEarly(s *model.Schema) *model.Schema {
	if s == nil {
		return nil
	}
	out := cloneSchema(s)
	for k, prop := range out.Properties {
		if prop.Default != nil {
			out.Required = append(out.Required, k)
		}
		out.Properties[k] = ApplyDefaultsEarly(prop)
	}
	if len(out.AllOf) > 0 {
		parts := make([]*model.Schema, len(out.AllOf))
		for i, part := range out.AllOf {
			parts[i] = ApplyDefaultsEarly(part)
		}
		out.AllOf = parts
	}
	return out
}

func HasDefault(s *model.Schema, field string) bool {
	if s == nil || s.Properties == nil {
		return false
	}
	prop, ok := s.Properties[field]
	return ok && prop.Default != nil
}
