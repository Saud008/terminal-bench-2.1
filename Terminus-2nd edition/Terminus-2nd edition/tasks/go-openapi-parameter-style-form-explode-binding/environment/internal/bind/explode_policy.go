package bind

import "github.com/terminus/paramgate/internal/openapi"

// explodeValue resolves OpenAPI style/explode defaults for query binding.
func explodeValue(p openapi.Parameter) bool {
	if p.Explode != nil {
		return *p.Explode
	}
	switch p.Style {
	case "deepObject":
		return false
	case "form":
		return false
	default:
		return false
	}
}
