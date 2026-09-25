package plugins

import (
	"strings"

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
		ctx.StopChain = true
		return false, nil
	}
	return true, nil
}
