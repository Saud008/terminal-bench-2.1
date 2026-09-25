package gateway

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/terminus/kongadmit/internal/chain"
	"github.com/terminus/kongadmit/internal/match"
	"github.com/terminus/kongadmit/internal/model"
	"github.com/terminus/kongadmit/internal/store"
)

type Proxy struct {
	Store        *store.Store
	UpstreamEcho string
}

func (p *Proxy) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if strings.HasPrefix(r.URL.Path, "/upstream/") {
		p.echoUpstream(w, r)
		return
	}
	services, routes, _ := p.Store.Snapshot()
	mr, ok := match.Select(routes, services, model.MatchRequest{Method: r.Method, Path: r.URL.Path})
	if !ok {
		http.Error(w, "no route", http.StatusNotFound)
		return
	}
	if !methodAllowed(mr.Route.Methods, r.Method) {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	rec := &captureWriter{header: make(http.Header), status: http.StatusOK}
	rec.header.Set("X-Matched-Route", mr.Route.Name)
	p.echoUpstream(rec, r)

	resp := &http.Response{
		StatusCode: rec.status,
		Header:     rec.header,
		Body:       http.NoBody,
		Request:    r,
	}
	if err := chain.Run(p.Store, mr, r, resp); err != nil {
		if resp.StatusCode == http.StatusUnauthorized {
			http.Error(w, err.Error(), http.StatusUnauthorized)
			return
		}
		if resp.StatusCode == http.StatusTooManyRequests {
			for k, vals := range resp.Header {
				for _, v := range vals {
					w.Header().Add(k, v)
				}
			}
			http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
			return
		}
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}
	for k, vals := range resp.Header {
		for _, v := range vals {
			w.Header().Add(k, v)
		}
	}
	w.WriteHeader(resp.StatusCode)
	_, _ = w.Write(rec.body)
}

func methodAllowed(methods []string, reqMethod string) bool {
	if len(methods) == 0 {
		return true
	}
	for _, m := range methods {
		if strings.EqualFold(m, reqMethod) {
			return true
		}
	}
	return false
}

func (p *Proxy) echoUpstream(w http.ResponseWriter, r *http.Request) {
	payload := map[string]any{
		"path":   r.URL.Path,
		"method": r.Method,
	}
	body, _ := json.Marshal(payload)
	if cw, ok := w.(*captureWriter); ok {
		cw.body = body
		cw.header.Set("Content-Type", "application/json")
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(body)
}

type captureWriter struct {
	header http.Header
	body   []byte
	status int
}

func (c *captureWriter) Header() http.Header {
	return c.header
}

func (c *captureWriter) Write(b []byte) (int, error) {
	c.body = append(c.body, b...)
	return len(b), nil
}

func (c *captureWriter) WriteHeader(statusCode int) {
	c.status = statusCode
}
