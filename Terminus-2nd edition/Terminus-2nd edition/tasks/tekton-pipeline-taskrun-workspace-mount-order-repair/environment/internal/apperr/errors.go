package apperr

import "errors"

var (
	ErrInvalidDocument = errors.New("invalid pipelinerun document")
	ErrCycleDetected   = errors.New("runAfter cycle detected")
	ErrMissingBinding  = errors.New("required workspace binding missing")
)
