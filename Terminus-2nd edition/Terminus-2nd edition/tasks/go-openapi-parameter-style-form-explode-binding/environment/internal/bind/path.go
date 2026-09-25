package bind

import (
	"net/http"
	"strings"

	"github.com/terminus/paramgate/internal/apperr"
	"github.com/terminus/paramgate/internal/openapi"
)

func (b *Binder) bindPath(r *http.Request, routePath string, params []openapi.Parameter, out map[string]any) error {
	segments := strings.Split(strings.Trim(routePath, "/"), "/")
	reqSegments := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
	if len(segments) != len(reqSegments) {
		return apperr.ErrBadParameter
	}
	for i, seg := range segments {
		if strings.HasPrefix(seg, "{") && strings.HasSuffix(seg, "}") {
			name := seg[1 : len(seg)-1]
			out[name] = reqSegments[i]
		}
	}
	for _, p := range params {
		if p.In != "path" {
			continue
		}
		val, ok := out[p.Name]
		if !ok || val == "" {
			if p.Required {
				return apperr.ErrMissingRequired
			}
		}
	}
	return nil
}
