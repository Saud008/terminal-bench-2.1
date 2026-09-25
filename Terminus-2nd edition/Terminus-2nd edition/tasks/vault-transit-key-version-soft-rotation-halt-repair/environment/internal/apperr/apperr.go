package apperr

import "errors"

var (
	ErrNotFound     = errors.New("not found")
	ErrBadRequest   = errors.New("bad request")
	ErrForbidden    = errors.New("forbidden")
	ErrRetired      = errors.New("retired version")
	ErrBelowMin     = errors.New("below min decryption version")
	ErrInvalidPolicy = errors.New("invalid policy")
)
