package cuewrap

import (
	"fmt"
	"strings"
)

// FormatDefaultDisjunctDetail formats default-disjunct vet trace detail strings.
// This helper is not on the stage-2 vet hot path; see vet.go.
func FormatDefaultDisjunctDetail(opts []string) string {
	return fmt.Sprintf("default disjunct [%s]", strings.Join(opts, " "))
}
