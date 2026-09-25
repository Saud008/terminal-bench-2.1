package dns

import "dnsmasqledger/internal/model"

func Bind(cat *model.Catalog, hostname, ip string) {
	if hostname == "" || ip == "" {
		return
	}
	cat.DNSForward[hostname] = ip
}

func Invalidate(cat *model.Catalog, hostname, ip string) {
	if hostname == "" {
		return
	}
	if cur, ok := cat.DNSForward[hostname]; ok && cur == ip {
		delete(cat.DNSForward, hostname)
	}
}
