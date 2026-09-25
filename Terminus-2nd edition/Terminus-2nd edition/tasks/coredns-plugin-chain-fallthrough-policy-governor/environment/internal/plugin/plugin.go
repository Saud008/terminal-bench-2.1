package plugin

import "github.com/terminus/dnsplugd/internal/model"

type Plugin interface {
	Name() string
	Serve(ctx *model.QueryCtx) (cont bool, err error)
}
