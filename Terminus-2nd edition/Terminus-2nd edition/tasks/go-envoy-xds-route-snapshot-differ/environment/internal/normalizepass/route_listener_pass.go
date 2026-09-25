package normalizepass

import (
	"sort"

	"github.com/terminus/xsnapctl/internal/lischain"
	"github.com/terminus/xsnapctl/internal/model"
	"github.com/terminus/xsnapctl/internal/routewin"
)

func applyRouteListenerPass(out *model.Snapshot) {
	for li := range out.Listeners {
		for ci := range out.Listeners[li].FilterChains {
			out.Listeners[li].FilterChains[ci].Filters = lischain.OrderFilters(
				out.Listeners[li].FilterChains[ci].Filters,
			)
		}
	}
	for ri := range out.Routes {
		out.Routes[ri].Routes = routewin.SelectWinningRoutes(out.Routes[ri].Routes)
		sort.Slice(out.Routes[ri].Routes, func(i, j int) bool {
			return out.Routes[ri].Routes[i].Cluster < out.Routes[ri].Routes[j].Cluster
		})
	}
}
