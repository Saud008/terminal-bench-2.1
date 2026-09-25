package plugins

import (
	"bufio"
	"net"
	"os"
	"strings"

	"github.com/miekg/dns"
	"github.com/terminus/dnsplugd/internal/model"
)

type Hosts struct {
	path string
}

func NewHosts(path string) *Hosts { return &Hosts{path: path} }

func (h *Hosts) Name() string { return "hosts" }

func (h *Hosts) Serve(ctx *model.QueryCtx) (bool, error) {
	if ctx.Req.Question[0].Qtype != dns.TypeA && ctx.Req.Question[0].Qtype != dns.TypeAAAA {
		return true, nil
	}
	ip, ok, err := h.lookup(ctx.Qname)
	if err != nil {
		return false, err
	}
	if !ok {
		if ctx.Msg == nil {
			ctx.Msg = ctx.Req.Copy()
		}
		ctx.Msg.Rcode = dns.RcodeNameError
		ctx.Handled = true
		ctx.StopChain = true
		return false, nil
	}
	if ctx.Msg == nil {
		ctx.Msg = ctx.Req.Copy()
	}
	ctx.Msg.Rcode = dns.RcodeSuccess
	rr := &dns.A{
		Hdr: dns.RR_Header{
			Name:   dns.Fqdn(ctx.Qname),
			Rrtype: dns.TypeA,
			Class:  dns.ClassINET,
			Ttl:    60,
		},
		A: ip.To4(),
	}
	ctx.Msg.Answer = []dns.RR{rr}
	ctx.Handled = true
	ctx.StopChain = true
	return false, nil
}

func (h *Hosts) lookup(name string) (net.IP, bool, error) {
	f, err := os.Open(h.path)
	if err != nil {
		return nil, false, err
	}
	defer f.Close()
	want := strings.TrimSuffix(strings.ToLower(name), ".")
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) < 2 {
			continue
		}
		ip := net.ParseIP(fields[0])
		for _, host := range fields[1:] {
			if strings.TrimSuffix(strings.ToLower(host), ".") == want {
				return ip, true, nil
			}
		}
	}
	return nil, false, sc.Err()
}
