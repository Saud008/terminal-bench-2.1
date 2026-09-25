package attribute

import "github.com/terminus/radiusproxy/internal/model"

func EffectiveInterimSec(pkt model.Packet, defaultSec int) int {
	if pkt.InterimInterval > 0 {
		return pkt.InterimInterval
	}
	if pkt.SessionTimeout > 0 {
		return pkt.SessionTimeout
	}
	return defaultSec
}
