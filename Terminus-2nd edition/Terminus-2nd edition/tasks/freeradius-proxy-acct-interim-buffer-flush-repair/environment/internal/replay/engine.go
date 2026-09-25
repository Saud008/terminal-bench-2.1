package replay

import (
	"os"

	"github.com/terminus/radiusproxy/internal/apperr"
	"github.com/terminus/radiusproxy/internal/attribute"
	"github.com/terminus/radiusproxy/internal/config"
	"github.com/terminus/radiusproxy/internal/model"
	"github.com/terminus/radiusproxy/internal/parse"
	"github.com/terminus/radiusproxy/internal/proxy"
	"github.com/terminus/radiusproxy/internal/session"
	"github.com/terminus/radiusproxy/internal/staging"
	"github.com/terminus/radiusproxy/internal/store"
)

var flushedRows []model.FlushEntry

func Run(logsDir, cfgPath, snapshotPath, dbPath string) (int, error) {
	cfg, err := config.Load(cfgPath)
	if err != nil {
		return apperr.ExitError, err
	}
	files, err := resolveLogFiles(logsDir)
	if err != nil {
		return apperr.ExitError, err
	}

	state := &model.ProxyState{
		ProxyName:  cfg.ProxyName,
		HomeServer: cfg.HomeServer,
		Sessions:   map[model.SessionKey]*model.SessionState{},
		ByNAS:      map[string]map[string]string{},
	}
	stats := model.Stats{}
	flushedRows = nil

	for _, file := range files {
		if err := parse.ReadLines(file, func(line string) error {
			stats.LinesRead++
			pkt, err := parse.ParseLine(line)
			if err != nil {
				stats.ParseErrors++
				return nil
			}
			return applyPacket(pkt, cfg, state, &stats)
		}); err != nil {
			return apperr.ExitError, err
		}
	}

	snap := staging.Build(state, stats)
	ck, err := store.PersistSnapshot(dbPath, snap, flushedRows)
	if err != nil {
		return apperr.ExitError, err
	}
	stats.WALCheckpoints += ck
	if err := staging.Write(snapshotPath, state, stats); err != nil {
		return apperr.ExitError, err
	}
	return apperr.ExitOK, nil
}

func resolveLogFiles(path string) ([]string, error) {
	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}
	if !info.IsDir() {
		return []string{path}, nil
	}
	return parse.DiscoverJSONL(path)
}

func applyPacket(pkt model.Packet, cfg config.Config, state *model.ProxyState, stats *model.Stats) error {
	if pkt.NASID == "" || pkt.AcctSessionID == "" || pkt.AcctStatusType == "" {
		stats.ParseErrors++
		return nil
	}
	interimSec := attribute.EffectiveInterimSec(pkt, cfg.DefaultInterimInterval)

	switch pkt.AcctStatusType {
	case "Start":
		sess := session.OnStart(state, pkt, interimSec, stats)
		sess.InputOctets = pkt.InputOctets
		sess.OutputOctets = pkt.OutputOctets
		stats.PacketsApplied++
	case "Interim-Update":
		sess := session.LookupOrStart(state, pkt, interimSec, stats)
		sess.InputOctets = pkt.InputOctets
		sess.OutputOctets = pkt.OutputOctets
		sess.LastInterimTS = pkt.TS
		stats.InterimBuffered++
		entry := model.FlushEntry{
			SessionStartTS: sess.SessionStartTS,
			Seq:            pkt.Seq,
			AcctStatusType: pkt.AcctStatusType,
			NASID:          pkt.NASID,
			AcctSessionID:  pkt.AcctSessionID,
		}
		proxy.Enqueue(state, entry)
		due := proxy.FlushDue(state, pkt.TS, stats)
		flushedRows = append(flushedRows, due...)
		stats.PacketsApplied++
	case "Stop":
		sess := session.LookupOrStart(state, pkt, interimSec, stats)
		sess.InputOctets = pkt.InputOctets
		sess.OutputOctets = pkt.OutputOctets
		sess.Status = "stopped"
		stats.SessionsStopped++
		pending := proxy.FlushPendingForStop(state, sess, pkt.TS, stats)
		flushedRows = append(flushedRows, pending...)
		due := proxy.FlushDue(state, pkt.TS, stats)
		flushedRows = append(flushedRows, due...)
		stats.PacketsApplied++
	default:
		stats.ProxyErrors++
	}
	return nil
}
