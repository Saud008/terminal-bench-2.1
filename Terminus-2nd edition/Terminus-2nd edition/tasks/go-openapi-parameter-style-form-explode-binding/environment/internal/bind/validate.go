package bind

import (
	"errors"
	"net/http"

	"github.com/terminus/paramgate/internal/apperr"
)

func StatusForBindErr(err error) int {
	if err == nil {
		return http.StatusOK
	}
	if errors.Is(err, apperr.ErrMissingRequired) {
		return http.StatusInternalServerError
	}
	if errors.Is(err, apperr.ErrBadContentType) || errors.Is(err, apperr.ErrBadParameter) {
		return http.StatusBadRequest
	}
	return http.StatusInternalServerError
}

func ReasonForBindErr(err error) string {
	switch {
	case errors.Is(err, apperr.ErrMissingRequired):
		return "missing_required"
	case errors.Is(err, apperr.ErrBadContentType):
		return "bad_content_type"
	case errors.Is(err, apperr.ErrBadParameter):
		return "invalid_parameter"
	default:
		return "internal_error"
	}
}
