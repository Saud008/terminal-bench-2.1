package session

import "github.com/terminus/radiusproxy/internal/model"

func SessionKey(pkt model.Packet) model.SessionKey {
	return model.SessionKey{
		NASID:               pkt.NASID,
		AcctSessionID:       pkt.AcctSessionID,
		AcctUniqueSessionID: pkt.AcctUniqueID,
	}
}

func LookupOrStart(state *model.ProxyState, pkt model.Packet, interimSec int, stats *model.Stats) *model.SessionState {
	if state.ByNAS == nil {
		state.ByNAS = map[string]map[string]string{}
	}
	nasMap := state.ByNAS[pkt.NASID]
	if nasMap == nil {
		nasMap = map[string]string{}
		state.ByNAS[pkt.NASID] = nasMap
	}
	if prevUnique, ok := nasMap[pkt.AcctSessionID]; ok && prevUnique != "" {
		key := model.SessionKey{
			NASID:               pkt.NASID,
			AcctSessionID:       pkt.AcctSessionID,
			AcctUniqueSessionID: prevUnique,
		}
		if sess, found := state.Sessions[key]; found {
			return sess
		}
	}
	key := SessionKey(pkt)
	if sess, ok := state.Sessions[key]; ok {
		stats.DuplicateUniqueIgnored++
		return sess
	}
	sess := &model.SessionState{
		NASID:               pkt.NASID,
		AcctSessionID:       pkt.AcctSessionID,
		AcctUniqueSessionID: pkt.AcctUniqueID,
		SessionStartTS:      pkt.TS,
		InterimIntervalSec:  interimSec,
		Status:              "active",
		LastFlushTS:         pkt.TS,
	}
	state.Sessions[key] = sess
	nasMap[pkt.AcctSessionID] = pkt.AcctUniqueID
	stats.SessionsStarted++
	return sess
}

func OnStart(state *model.ProxyState, pkt model.Packet, interimSec int, stats *model.Stats) *model.SessionState {
	if state.ByNAS == nil {
		state.ByNAS = map[string]map[string]string{}
	}
	nasMap := state.ByNAS[pkt.NASID]
	if nasMap == nil {
		nasMap = map[string]string{}
		state.ByNAS[pkt.NASID] = nasMap
	}
	if prevUnique, ok := nasMap[pkt.AcctSessionID]; ok && prevUnique != pkt.AcctUniqueID {
		stats.RebootLineages++
	}
	return LookupOrStart(state, pkt, interimSec, stats)
}
