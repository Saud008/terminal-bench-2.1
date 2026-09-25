package bind

import "github.com/terminus/paramgate/internal/openapi"

type Result struct {
	Params map[string]any `json:"params"`
	Body   map[string]any `json:"body,omitempty"`
}

type Binder struct {
	Spec openapi.Document
}

func New(spec openapi.Document) *Binder {
	return &Binder{Spec: spec}
}
