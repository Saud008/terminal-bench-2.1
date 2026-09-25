# DHCP renew on roam

During DHCP_RENEW after ASSOCIATING, set dhcp_gateway from target_bss.gateway when scan_credited is true and a service is selected.

When scan_credited is false or no service is selected, dhcp_gateway must fall back to current_bss.gateway.

Do not reuse current_bss.gateway after a credited scan and service selection when roam should complete.

handoff_success requires dhcp_gateway equals target_bss.gateway when scan_credited is true and a service is selected.

Fixture example: stale-gateway-trap sets dhcp_gateway to 10.44.0.1 when the scan is credited.
