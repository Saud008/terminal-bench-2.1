package negotiate

import (
	"strings"

	"github.com/terminus/variantgate/internal/model"
)

func Prepare(in model.NegotiationInput) model.NegotiationInput {
	out := in
	if strings.TrimSpace(out.Accept) == "" {
		out.Accept = "*/*"
	}
	if strings.TrimSpace(out.AcceptLanguage) == "" {
		out.AcceptLanguage = "*"
	}
	return out
}
