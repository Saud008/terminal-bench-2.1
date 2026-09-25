package plugins

import (
	"fmt"
	"strings"

	"github.com/miekg/dns"
	"github.com/terminus/dnsplugd/internal/model"
)

type Rewrite struct {
	rule model.RewriteRule
}

func NewRewrite(rule model.RewriteRule) *Rewrite {
	return &Rewrite{rule: rule}
}

func (r *Rewrite) Name() string { return "rewrite" }

func (r *Rewrite) Serve(ctx *model.QueryCtx) (bool, error) {
	before := ctx.Qname
	switch r.rule.Mode {
	case "suffix":
		if strings.HasSuffix(before, r.rule.From) {
			ctx.Qname = strings.TrimSuffix(before, r.rule.From) + r.rule.To
		}
	case "exact":
		if before == r.rule.From {
			ctx.Qname = r.rule.To
		}
	}
	if ctx.Qname != before {
		ctx.Handled = true
		if r.rule.Continue {
			return true, nil
		}
		ctx.StopChain = true
		return false, nil
	}
	return true, nil
}

func addCNAMEResponse(ctx *model.QueryCtx, target string) {
	if ctx.Msg == nil {
		ctx.Msg = ctx.Req.Copy()
	}
	ctx.Msg.Rcode = dns.RcodeSuccess
	rr := &dns.CNAME{
		Hdr: dns.RR_Header{
			Name:   dns.Fqdn(ctx.Req.Question[0].Name),
			Rrtype: dns.TypeCNAME,
			Class:  dns.ClassINET,
			Ttl:    60,
		},
		Target: dns.Fqdn(target),
	}
	ctx.Msg.Answer = []dns.RR{rr}
}

var _ = fmt.Sprintf
