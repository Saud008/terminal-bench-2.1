package deref

import (
	"fmt"

	"github.com/terminus/oasctl/internal/model"
)

func ApplyDiscriminator(base *model.Schema, data map[string]any, components map[string]*model.Schema) (*model.Schema, int) {
	if base == nil || base.Discriminator == nil {
		return base, 0
	}
	raw, ok := data[base.Discriminator.PropertyName]
	if !ok {
		return base, 0
	}
	key := fmt.Sprint(raw)
	sub := components[key]
	if sub == nil {
		return base, 0
	}
	resolved, cycles := Resolve(sub, components, nil)
	return MergeSchemas(base, resolved), cycles
}
