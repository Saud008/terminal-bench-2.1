package ingest

import (
	"github.com/terminus/vicireplay/internal/config"
	"github.com/terminus/vicireplay/internal/model"
)

func NormalizeTrace(tr model.Trace) model.Trace {
	out := tr
	if out.GatewayID == "" {
		out.GatewayID = "gw-local"
	}
	offset := config.InitiatorOffset()
	for i := range out.Events {
		if out.Events[i].IkeUniqueID > 0 {
			out.Events[i].IkeUniqueID += offset
		}
		if out.Events[i].ChildUniqueID > 0 {
			out.Events[i].ChildUniqueID += offset
		}
	}
	return out
}
