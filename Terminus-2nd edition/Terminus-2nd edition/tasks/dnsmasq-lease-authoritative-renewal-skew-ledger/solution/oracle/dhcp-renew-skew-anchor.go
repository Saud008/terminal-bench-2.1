package lease

import (
	"dnsmasqledger/internal/identity"
	"dnsmasqledger/internal/model"
)

func Renew(cat *model.Catalog, ev model.ReplayEvent) bool {
	key := identity.IdentityKey(ev.MAC, ev.DUID, ev.IAID)
	l, ok := cat.Leases[key]
	if !ok || !l.Authoritative {
		return false
	}
	leaseSec := ev.LeaseSec
	if leaseSec <= 0 {
		leaseSec = l.LeaseSec
	}
	l.ExpiresSec = l.ExpiresSec + leaseSec
	l.LeaseSec = leaseSec
	return true
}
