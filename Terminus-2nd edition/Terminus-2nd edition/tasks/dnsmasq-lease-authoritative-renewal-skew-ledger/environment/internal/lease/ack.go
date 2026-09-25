package lease

import (
	"dnsmasqledger/internal/dns"
	"dnsmasqledger/internal/identity"
	"dnsmasqledger/internal/model"
)

func Ack(cat *model.Catalog, ev model.ReplayEvent, replay bool) bool {
	key := identity.IdentityKey(ev.MAC, ev.DUID, ev.IAID)
	if key == "" || ev.IP == "" {
		return false
	}
	prev, had := cat.Leases[key]
	oldIP := ""
	oldHost := ""
	if had {
		oldIP = prev.IP
		oldHost = prev.Hostname
	}

	leaseSec := ev.LeaseSec
	if leaseSec <= 0 && had {
		leaseSec = prev.LeaseSec
	}
	if leaseSec <= 0 {
		leaseSec = 3600
	}

	auth := true
	if had {
		auth = !prev.Authoritative
	}

	hostname := ev.Hostname
	if hostname == "" && had {
		hostname = prev.Hostname
	}
	if hostname == "" {
		if t, ok := cat.Tentative[key]; ok {
			hostname = t.Hostname
		}
	}

	cat.Leases[key] = &model.Lease{
		IdentityKey:   key,
		MAC:           ev.MAC,
		DUID:          ev.DUID,
		IAID:          ev.IAID,
		Hostname:      hostname,
		IP:            ev.IP,
		LeaseSec:      leaseSec,
		ExpiresSec:    cat.NowSec + leaseSec,
		Authoritative: auth,
		Tentative:     false,
	}
	delete(cat.Tentative, key)

	if had && oldIP != ev.IP && oldHost != "" {
		dns.Invalidate(cat, oldHost, oldIP)
	}
	if hostname != "" {
		dns.Bind(cat, hostname, ev.IP)
	}
	_ = replay
	return true
}
