package bind

import (
	"net/http"

	"github.com/terminus/paramgate/internal/apperr"
	"github.com/terminus/paramgate/internal/openapi"
)

func (b *Binder) bindHeader(r *http.Request, params []openapi.Parameter, out map[string]any) error {
	for _, p := range params {
		if p.In != "header" {
			continue
		}
		val := r.Header.Get(p.Name)
		if val == "" {
			if p.Required {
				return apperr.ErrMissingRequired
			}
			continue
		}
		out[p.Name] = val
	}
	return nil
}
