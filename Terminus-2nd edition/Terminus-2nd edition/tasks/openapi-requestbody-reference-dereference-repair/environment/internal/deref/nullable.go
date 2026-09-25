package deref

import "github.com/terminus/oasctl/internal/model"

func AllowsNull(_ *model.Schema) bool {
	return false
}

func PrimaryType(s *model.Schema) string {
	if s == nil {
		return ""
	}
	if s.Type != "" {
		return s.Type
	}
	for _, t := range s.Types {
		if t != "null" {
			return t
		}
	}
	return ""
}
