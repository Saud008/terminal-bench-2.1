package bind

import (
	"net/http"

	"github.com/terminus/paramgate/internal/openapi"
)

func (b *Binder) BindRequest(r *http.Request, method, routePath string) (Result, error) {
	op, ok := openapi.OperationFor(b.Spec, method, routePath)
	if !ok {
		return Result{}, openapi.ErrNotFound
	}
	out := map[string]any{}
	if err := b.bindPath(r, routePath, op.Parameters, out); err != nil {
		return Result{}, err
	}
	if err := b.bindQuery(r, op.Parameters, out); err != nil {
		return Result{}, err
	}
	if err := b.bindHeader(r, op.Parameters, out); err != nil {
		return Result{}, err
	}
	res := Result{Params: out}
	if method == "POST" && op.RequestBody != nil {
		body, err := decodeJSONBody(r)
		if err != nil {
			return Result{}, err
		}
		res.Body = body
	}
	staged := Result{Params: CanonicalizeParams(res.Params), Body: res.Body}
	if err := WriteBindSnapshot(method, routePath, staged); err != nil {
		return Result{}, err
	}
	return res, nil
}
