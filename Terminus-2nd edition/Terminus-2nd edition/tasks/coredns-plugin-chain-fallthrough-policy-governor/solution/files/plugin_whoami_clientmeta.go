package plugins

import (
	"fmt"
	"net"
	"strings"

	"github.com/miekg/dns"
	"github.com/terminus/dnsplugd/internal/model"
)

type Whoami struct{}

func NewWhoami() *Whoami { return &Whoami{} }

func (w *Whoami) Name() string { return "whoami" }

func (w *Whoami) Serve(ctx *model.QueryCtx) (bool, error) {
	if ctx.Req.Question[0].Qtype != dns.TypeTXT {
		return true, nil
	}
	if strings.Contains(strings.ToLower(ctx.Qname), ".bad.") {
		return false, fmt.Errorf("whoami rejected qname")
	}
	ip := ctx.ClientIP
	if ip == "" || net.ParseIP(ip) == nil {
		return false, fmt.Errorf("whoami invalid client")
	}
	if ctx.Msg == nil {
		ctx.Msg = ctx.Req.Copy()
	}
	ctx.Msg.Rcode = dns.RcodeSuccess
	txt := &dns.TXT{
		Hdr: dns.RR_Header{
			Name:   dns.Fqdn(ctx.Qname),
			Rrtype: dns.TypeTXT,
			Class:  dns.ClassINET,
			Ttl:    30,
		},
		Txt: []string{fmt.Sprintf("client=%s", ip)},
	}
	ctx.Msg.Answer = []dns.RR{txt}
	ctx.Handled = true
	ctx.StopChain = true
	return false, nil
}
