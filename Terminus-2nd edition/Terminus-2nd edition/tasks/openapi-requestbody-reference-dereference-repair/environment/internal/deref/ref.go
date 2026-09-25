package deref

import (
	"strings"

	"github.com/terminus/oasctl/internal/model"
)

func RefName(ref string) string {
	parts := strings.Split(ref, "/")
	return parts[len(parts)-1]
}

func ResolveRef(ref string, components map[string]*model.Schema) *model.Schema {
	name := RefName(ref)
	s := components[name]
	if s == nil {
		return nil
	}
	if s.Ref != "" {
		return components[RefName(s.Ref)]
	}
	return cloneSchema(s)
}
