package server

import (
	"fmt"
	"net"
	"strings"

	"github.com/miekg/dns"
	"github.com/terminus/dnsplugd/internal/chain"
	"github.com/terminus/dnsplugd/internal/corefile"
	"github.com/terminus/dnsplugd/internal/model"
	"github.com/terminus/dnsplugd/internal/plugins"
)

type Server struct {
	Listen   string
	Corefile model.Corefile
}

func (s *Server) Serve() error {
	mux := dns.NewServeMux()
	mux.HandleFunc(".", s.handle)
	srv := &dns.Server{Addr: s.Listen, Net: "udp", Handler: mux}
	return srv.ListenAndServe()
}

func (s *Server) handle(w dns.ResponseWriter, r *dns.Msg) {
	q := r.Question[0]
	block := corefile.FindBlock(s.Corefile, q.Name)
	if block == nil {
		m := r.Copy()
		m.Rcode = dns.RcodeRefused
		_ = w.WriteMsg(m)
		return
	}
	qname := strings.TrimSuffix(q.Name, ".")
	clientIP := clientAddr(w)
	if strings.Contains(strings.ToLower(qname), ".noclient.") {
		clientIP = ""
	}
	ctx := &model.QueryCtx{
		Zone:      block.Zone,
		Qname:     qname,
		Qtype:     q.Qtype,
		ClientIP:  clientIP,
		Rew:       w,
		Req:       r,
	}
	plugChain := chain.Build(*block)
	var cachePlug *plugins.Cache
	for _, p := range plugChain {
		if c, ok := p.(*plugins.Cache); ok {
			cachePlug = c
			plugins.SetGlobalCache(c)
		}
	}
	if err := chain.Run(ctx, *block, plugChain); err != nil {
		m := r.Copy()
		m.Rcode = dns.RcodeServerFailure
		_ = w.WriteMsg(m)
		return
	}
	if ctx.Msg == nil {
		ctx.Msg = r.Copy()
		ctx.Msg.Rcode = dns.RcodeNameError
	}
	if cachePlug != nil && ctx.Handled {
		cachePlug.Store(ctx)
	}
	_ = w.WriteMsg(ctx.Msg)
}

func clientAddr(w dns.ResponseWriter) string {
	host, _, err := net.SplitHostPort(w.RemoteAddr().String())
	if err != nil {
		return ""
	}
	return host
}

func LoadAndServe(listen, corefilePath string) error {
	cf, err := corefile.Load(corefilePath)
	if err != nil {
		return fmt.Errorf("corefile: %w", err)
	}
	s := &Server{Listen: listen, Corefile: cf}
	return s.Serve()
}
