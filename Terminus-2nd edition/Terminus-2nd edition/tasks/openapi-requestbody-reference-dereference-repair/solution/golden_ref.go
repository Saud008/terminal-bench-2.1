package deref

import (
	"strings"

	"github.com/terminus/oasctl/internal/model"
)

func RefName(ref string) string {
	parts := strings.Split(ref, "/")
	return parts[len(parts)-1]
}

func ExpandRef(ref string, components map[string]*model.Schema, stack []string) (*model.Schema, int) {
	name := RefName(ref)
	if OnStack(stack, name) {
		return &model.Schema{Type: "object", Properties: map[string]*model.Schema{}}, 1
	}
	target := components[name]
	if target == nil {
		return nil, 0
	}
	return Resolve(target, components, append(stack, name))
}
