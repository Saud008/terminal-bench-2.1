package deref

import "github.com/terminus/oasctl/internal/model"

func MergeSchemas(parts ...*model.Schema) *model.Schema {
	out := &model.Schema{
		Type:       "object",
		Properties: map[string]*model.Schema{},
	}
	seenReq := map[string]bool{}
	for _, part := range parts {
		if part == nil {
			continue
		}
		for _, r := range part.Required {
			if !seenReq[r] {
				out.Required = append(out.Required, r)
				seenReq[r] = true
			}
		}
		for k, v := range part.Properties {
			if _, exists := out.Properties[k]; !exists {
				out.Properties[k] = cloneSchema(v)
			}
		}
		if part.Discriminator != nil {
			out.Discriminator = part.Discriminator
		}
		if part.AdditionalProperties != nil {
			out.AdditionalProperties = part.AdditionalProperties
		}
	}
	return out
}

func cloneSchema(s *model.Schema) *model.Schema {
	if s == nil {
		return nil
	}
	out := *s
	if s.Properties != nil {
		out.Properties = map[string]*model.Schema{}
		for k, v := range s.Properties {
			out.Properties[k] = cloneSchema(v)
		}
	}
	if s.AllOf != nil {
		out.AllOf = make([]*model.Schema, len(s.AllOf))
		for i, part := range s.AllOf {
			out.AllOf[i] = cloneSchema(part)
		}
	}
	if s.Discriminator != nil {
		d := *s.Discriminator
		d.Mapping = map[string]string{}
		for k, v := range s.Discriminator.Mapping {
			d.Mapping[k] = v
		}
		out.Discriminator = &d
	}
	if s.AdditionalProperties != nil {
		v := *s.AdditionalProperties
		out.AdditionalProperties = &v
	}
	if len(s.Types) > 0 {
		out.Types = append([]string(nil), s.Types...)
	}
	return &out
}
