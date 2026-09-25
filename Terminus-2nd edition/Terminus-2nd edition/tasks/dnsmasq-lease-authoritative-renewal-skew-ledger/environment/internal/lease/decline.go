package lease

import (
	"dnsmasqledger/internal/dns"
	"dnsmasqledger/internal/identity"
	"dnsmasqledger/internal/model"
)

func Decline(cat *model.Catalog, ev model.ReplayEvent) bool {
	key := identity.IdentityKey(ev.MAC, ev.DUID, ev.IAID)
	if key == "" {
		return false
	}
	if l, ok := cat.Leases[key]; ok {
		if l.Hostname != "" {
			dns.Invalidate(cat, l.Hostname, l.IP)
		}
		delete(cat.Leases, key)
	}
	return true
}

func Release(cat *model.Catalog, ev model.ReplayEvent) bool {
	key := identity.IdentityKey(ev.MAC, ev.DUID, ev.IAID)
	l, ok := cat.Leases[key]
	if !ok {
		return false
	}
	if l.Hostname != "" {
		dns.Invalidate(cat, l.Hostname, l.IP)
	}
	delete(cat.Leases, key)
	delete(cat.Tentative, key)
	return true
}

func ExpireDue(cat *model.Catalog) {
	for key, l := range cat.Leases {
		if cat.NowSec >= l.ExpiresSec {
			if l.Hostname != "" {
				dns.Invalidate(cat, l.Hostname, l.IP)
			}
			delete(cat.Leases, key)
		}
	}
	for key, t := range cat.Tentative {
		if t.ExpiresSec > 0 && cat.NowSec >= t.ExpiresSec {
			delete(cat.Tentative, key)
		}
	}
}

// WrapRenewSkew is a decoy helper — export hot path does not call this.
func WrapRenewSkew(base int64, skew int64) int64 {
	return base + skew
}
