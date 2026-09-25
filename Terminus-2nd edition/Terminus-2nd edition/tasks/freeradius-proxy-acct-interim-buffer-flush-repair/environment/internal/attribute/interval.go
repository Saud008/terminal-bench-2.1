package attribute

import "github.com/terminus/radiusproxy/internal/model"

// EffectiveInterimSec chooses the flush interval for interim accounting updates.
func EffectiveInterimSec(pkt model.Packet, defaultSec int) int {
	if pkt.SessionTimeout > 0 {
		return pkt.SessionTimeout
	}
	if pkt.InterimInterval > 0 {
		return pkt.InterimInterval
	}
	return defaultSec
}
