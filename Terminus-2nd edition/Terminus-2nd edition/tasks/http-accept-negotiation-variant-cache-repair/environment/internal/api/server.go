package api

import (
	"fmt"
	"net/http"
	"strings"

	"github.com/terminus/variantgate/internal/cache"
	"github.com/terminus/variantgate/internal/model"
	"github.com/terminus/variantgate/internal/negotiate"
	"github.com/terminus/variantgate/internal/staging"
	"github.com/terminus/variantgate/internal/variants"
)

const VaryHeader = "Accept, Accept-Language, Accept-Charset"

type Server struct {
	Store *variants.Store
	Cache *cache.ResponseCache
}

func New(store *variants.Store, c *cache.ResponseCache) *Server {
	return &Server{Store: store, Cache: c}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/cache/stats", s.handleCacheStats)
	mux.HandleFunc("/admin/catalog", s.handleAdminCatalog)
	mux.HandleFunc("/admin/negotiation/verify", s.handleNegotiationVerify)
	mux.HandleFunc("/resource/", s.handleResource)
	return mux
}

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(`{"status":"ok"}`))
}

func (s *Server) handleNegotiationVerify(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	snap, err := staging.Load(staging.DefaultPath)
	if err != nil {
		http.Error(w, "snapshot unavailable", http.StatusNotFound)
		return
	}
	aligned := staging.VerifySnapshot(snap) == nil
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	if aligned {
		_, _ = w.Write([]byte(`{"aligned":true}`))
		return
	}
	_, _ = w.Write([]byte(`{"aligned":false}`))
}

func (s *Server) handleCacheStats(w http.ResponseWriter, _ *http.Request) {
	stats := s.Cache.Stats()
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_, _ = fmt.Fprintf(w, `{"hits":%d,"misses":%d}`, stats.Hits, stats.Misses)
}

func (s *Server) handleResource(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	id := strings.TrimPrefix(r.URL.Path, "/resource/")
	if id == "" || strings.Contains(id, "/") {
		http.NotFound(w, r)
		return
	}
	res, ok := s.Store.Get(id)
	if !ok {
		http.NotFound(w, r)
		return
	}
	if prior, err := staging.Load(staging.DefaultPath); err == nil {
		if err := staging.VerifySnapshot(prior); err != nil {
			w.Header().Set("Vary", VaryHeader)
			w.Header().Set("X-Cache", "MISS")
			w.WriteHeader(http.StatusNotAcceptable)
			return
		}
	}
	raw := model.NegotiationInput{
		Accept:         r.Header.Get("Accept"),
		AcceptLanguage: r.Header.Get("Accept-Language"),
		AcceptCharset:  r.Header.Get("Accept-Charset"),
	}
	prepared := negotiate.Prepare(raw)
	path := r.URL.Path
	snap := staging.Record(path, id, raw, prepared)
	_ = staging.Write(staging.DefaultPath, snap)
	if cached, hit := s.Cache.Get(path, raw); hit {
		w.Header().Set("Vary", cached.Vary)
		w.Header().Set("Content-Type", cached.ContentType)
		w.Header().Set("X-Cache", "HIT")
		w.WriteHeader(cached.Status)
		_, _ = w.Write(cached.Body)
		return
	}

	sel, matched := staging.SelectFromSnapshot(snap, res.Variants)
	if !matched || sel == nil {
		w.Header().Set("Vary", VaryHeader)
		w.Header().Set("X-Cache", "MISS")
		w.WriteHeader(http.StatusNotAcceptable)
		s.Cache.Put(path, raw, cache.CachedResponse{
			Status:      http.StatusNotAcceptable,
			ContentType: "",
			Vary:        VaryHeader,
			Body:        nil,
		})
		return
	}
	body := []byte(sel.Variant.Body)
	contentType := fmt.Sprintf("%s; charset=%s", sel.MediaType, sel.Charset)
	w.Header().Set("Vary", VaryHeader)
	w.Header().Set("Content-Type", contentType)
	w.Header().Set("X-Cache", "MISS")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(body)
	s.Cache.Put(path, raw, cache.CachedResponse{
		Status:      http.StatusOK,
		ContentType: contentType,
		Vary:        VaryHeader,
		Body:        body,
	})
}
