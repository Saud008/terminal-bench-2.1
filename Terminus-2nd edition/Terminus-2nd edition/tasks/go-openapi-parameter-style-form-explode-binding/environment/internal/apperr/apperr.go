package apperr

import "errors"

var (
	ErrMissingRequired = errors.New("missing required parameter")
	ErrBadContentType  = errors.New("unsupported content type")
	ErrBadParameter    = errors.New("invalid parameter value")
)
