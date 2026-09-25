package checkpoint

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"dnsmasqledger/internal/model"
)

type snap struct {
	LogPath     string            `json:"log_path"`
	ThroughSeq  int               `json:"through_seq"`
	NowSec      int64             `json:"now_sec"`
	Leases      map[string]*model.Lease `json:"leases"`
	Tentative   map[string]*model.Tentative `json:"tentative"`
	DNSForward  map[string]string `json:"dns_forward"`
}

func statePath(logPath string) string {
	base := strings.TrimSuffix(filepath.Base(logPath), filepath.Ext(logPath))
	return filepath.Join("/app/state", "ckpt-"+base+".json")
}

func Load(logPath string) (*snap, error) {
	data, err := os.ReadFile(statePath(logPath))
	if err != nil {
		return nil, err
	}
	var s snap
	if err := json.Unmarshal(data, &s); err != nil {
		return nil, err
	}
	return &s, nil
}

func RestoreCatalog(cat *model.Catalog, s *snap) {
	cat.NowSec = s.NowSec
	cat.Leases = s.Leases
	cat.Tentative = s.Tentative
	cat.DNSForward = s.DNSForward
	cat.Checkpoint = s.ThroughSeq
}

func Persist(cat *model.Catalog, logPath string, throughSeq int) error {
	s := snap{
		LogPath:    logPath,
		ThroughSeq: throughSeq,
		NowSec:     cat.NowSec,
		Leases:     cat.Leases,
		Tentative:  cat.Tentative,
		DNSForward: cat.DNSForward,
	}
	data, err := json.Marshal(s)
	if err != nil {
		return err
	}
	return os.WriteFile(statePath(logPath), data, 0o644)
}

// PersistBeforeDNSInvalidation writes checkpoint before caller invalidates DNS.
func PersistBeforeDNSInvalidation(cat *model.Catalog, logPath string, throughSeq int) error {
	return Persist(cat, logPath, throughSeq)
}
