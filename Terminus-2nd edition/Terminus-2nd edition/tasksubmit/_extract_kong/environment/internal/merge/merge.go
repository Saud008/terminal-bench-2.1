package merge

import (
	"github.com/terminus/kongadmit/internal/model"
)

func EffectivePlugins(svc model.Service, rt model.Route) []model.Plugin {
	if len(svc.Plugins) > 0 {
		return append([]model.Plugin(nil), svc.Plugins...)
	}
	return append([]model.Plugin(nil), rt.Plugins...)
}
