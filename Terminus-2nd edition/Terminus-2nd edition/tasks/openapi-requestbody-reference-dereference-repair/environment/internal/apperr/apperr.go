package apperr

import "errors"

var (
	ErrIO        = errors.New("io error")
	ErrConfig    = errors.New("invalid config")
	ErrParse     = errors.New("parse error")
	ErrOperation = errors.New("unknown operation")
)
