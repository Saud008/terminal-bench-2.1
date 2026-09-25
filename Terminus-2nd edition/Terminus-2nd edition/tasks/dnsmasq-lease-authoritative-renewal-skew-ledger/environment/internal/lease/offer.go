package lease

import (
	"dnsmasqledger/internal/identity"
	"dnsmasqledger/internal/model"
)

func Discover(cat *model.Catalog, ev model.ReplayEvent) bool {
	key := identity.IdentityKey(ev.MAC, ev.DUID, ev.IAID)
	if key == "" {
		return false
	}
	cat.Tentative[key] = &model.Tentative{
		IdentityKey: key,
		MAC:         ev.MAC,
		DUID:        ev.DUID,
		IAID:        ev.IAID,
		Hostname:    ev.Hostname,
	}
	return true
}

func Offer(cat *model.Catalog, ev model.ReplayEvent) bool {
	key := identity.IdentityKey(ev.MAC, ev.DUID, ev.IAID)
	t, ok := cat.Tentative[key]
	if !ok {
		return false
	}
	t.IP = ev.IP
	t.LeaseSec = ev.LeaseSec
	t.ExpiresSec = cat.NowSec + ev.LeaseSec
	return true
}
