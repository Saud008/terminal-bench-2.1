package proof

import (
	"strings"

	"nsecval/internal/wire"
)

// ClosestEncloser returns the closest encloser name for a wildcard proof (decoy helper).
func ClosestEncloser(qname, zone string) string {
	qname = wire.Canonical(wire.EnsureTrailingDot(qname))
	zone = wire.Canonical(wire.EnsureTrailingDot(zone))
	if qname == zone {
		return zone
	}
	trimmed := strings.TrimSuffix(qname, ".")
	parts := strings.Split(trimmed, ".")
	zoneTrim := strings.TrimSuffix(zone, ".")
	zoneParts := strings.Split(zoneTrim, ".")
	if len(parts) <= len(zoneParts) {
		return zone
	}
	encloserParts := parts[:len(parts)-1]
	return wire.Canonical(strings.Join(encloserParts, ".") + ".")
}

func WildcardAtEncloser(encloser string) string {
	encloser = wire.EnsureTrailingDot(encloser)
	if encloser == "." {
		return "*."
	}
	return "*." + strings.TrimSuffix(encloser, ".")
}
