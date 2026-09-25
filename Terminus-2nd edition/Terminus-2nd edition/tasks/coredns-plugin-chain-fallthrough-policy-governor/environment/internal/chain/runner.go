package chain

import (
	"strings"

	"github.com/miekg/dns"
	"github.com/terminus/dnsplugd/internal/model"
	"github.com/terminus/dnsplugd/internal/plugin"
)

func Run(ctx *model.QueryCtx, block model.ServerBlock, chain []plugin.Plugin) error {
	if ctx.Msg == nil {
		ctx.Msg = ctx.Req.Copy()
	}
	for _, p := range chain {
		if ctx.StopChain {
			break
		}
		cont, err := p.Serve(ctx)
		if err != nil {
			ctx.Msg = ctx.Req.Copy()
			ctx.Msg.Rcode = dns.RcodeServerFailure
			ctx.Handled = true
			ctx.StopChain = true
			return nil
		}
		if ctx.Handled && !cont {
			return nil
		}
		effective := strings.TrimSuffix(ctx.Req.Question[0].Name, ".")
		if !cont && !AllowsFallthrough(block.Zone, effective, block.Fallthrough) {
			return nil
		}
	}
	if !ctx.Handled {
		ctx.Msg = ctx.Req.Copy()
		ctx.Msg.Rcode = dns.RcodeNameError
	}
	return nil
}
