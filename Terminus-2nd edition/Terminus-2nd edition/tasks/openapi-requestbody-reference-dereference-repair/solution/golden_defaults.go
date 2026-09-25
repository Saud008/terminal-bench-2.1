package deref

import "github.com/terminus/oasctl/internal/model"

func HasDefault(s *model.Schema, field string) bool {
	if s == nil || s.Properties == nil {
		return false
	}
	prop, ok := s.Properties[field]
	return ok && prop.Default != nil
}
