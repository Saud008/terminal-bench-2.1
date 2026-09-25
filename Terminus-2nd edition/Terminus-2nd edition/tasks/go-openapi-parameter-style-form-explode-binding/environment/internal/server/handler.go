package server

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"github.com/terminus/paramgate/internal/bind"
	"github.com/terminus/paramgate/internal/openapi"
)

type Handler struct {
	Binder *bind.Binder
	Routes map[string]string
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	routePath, ok := matchRoute(r.URL.Path, h.Routes)
	if !ok {
		writeJSON(w, http.StatusNotFound, map[string]any{"status": "not_found"})
		return
	}
	res, err := h.Binder.BindRequest(r, r.Method, routePath)
	if err != nil {
		if errors.Is(err, openapi.ErrNotFound) {
			writeJSON(w, http.StatusNotFound, map[string]any{"status": "not_found"})
			return
		}
		status := bind.StatusForBindErr(err)
		writeJSON(w, status, map[string]any{
			"status": "invalid",
			"reason": bind.ReasonForBindErr(err),
		})
		return
	}
	payload, err := bind.EmitSuccess(res)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]any{"status": "internal_error"})
		return
	}
	writeJSON(w, http.StatusOK, payload)
}

func matchRoute(reqPath string, routes map[string]string) (string, bool) {
	if route, ok := routes[reqPath]; ok {
		return route, true
	}
	reqSegs := strings.Split(strings.Trim(reqPath, "/"), "/")
	for pattern, route := range routes {
		patSegs := strings.Split(strings.Trim(pattern, "/"), "/")
		if len(patSegs) != len(reqSegs) {
			continue
		}
		matched := true
		for i := range patSegs {
			if strings.HasPrefix(patSegs[i], "{") && strings.HasSuffix(patSegs[i], "}") {
				continue
			}
			if patSegs[i] != reqSegs[i] {
				matched = false
				break
			}
		}
		if matched {
			return route, true
		}
	}
	return "", false
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
