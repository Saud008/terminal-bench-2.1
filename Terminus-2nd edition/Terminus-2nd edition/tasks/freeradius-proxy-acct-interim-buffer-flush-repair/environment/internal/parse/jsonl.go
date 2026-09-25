package parse

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"strconv"

	"github.com/terminus/radiusproxy/internal/model"
)

func DiscoverJSONL(dir string) ([]string, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var out []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		if filepath.Ext(e.Name()) == ".jsonl" {
			out = append(out, filepath.Join(dir, e.Name()))
		}
	}
	sort.Strings(out)
	return out, nil
}

func ReadLines(path string, fn func(string) error) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Text()
		if line == "" {
			continue
		}
		if err := fn(line); err != nil {
			return err
		}
	}
	return sc.Err()
}

func ParseLine(line string) (model.Packet, error) {
	var raw map[string]any
	if err := json.Unmarshal([]byte(line), &raw); err != nil {
		return model.Packet{}, err
	}
	p := model.Packet{
		TS:             int64(num(raw["ts"])),
		Seq:            int(num(raw["seq"])),
		NASID:          str(raw["nas_id"]),
		AcctStatusType: str(raw["acct_status_type"]),
	}
	if attrs, ok := raw["attrs"].(map[string]any); ok {
		p.AcctSessionID = str(attrs["Acct-Session-Id"])
		p.AcctUniqueID = str(attrs["Acct-Unique-Session-Id"])
		p.SessionTimeout = int(num(attrs["Session-Timeout"]))
		p.InterimInterval = int(num(attrs["Acct-Interim-Interval"]))
		p.InputOctets = int64(num(attrs["Acct-Input-Octets"]))
		p.OutputOctets = int64(num(attrs["Acct-Output-Octets"]))
		p.AcctSessionTime = int(num(attrs["Acct-Session-Time"]))
		p.NASReboot = boolVal(attrs["NAS-Reboot"])
	}
	return p, nil
}

func str(v any) string {
	if v == nil {
		return ""
	}
	switch t := v.(type) {
	case string:
		return t
	default:
		return ""
	}
}

func num(v any) float64 {
	switch t := v.(type) {
	case float64:
		return t
	case int:
		return float64(t)
	case int64:
		return float64(t)
	case json.Number:
		f, _ := t.Float64()
		return f
	case string:
		f, _ := strconv.ParseFloat(t, 64)
		return f
	default:
		return 0
	}
}

func boolVal(v any) bool {
	switch t := v.(type) {
	case bool:
		return t
	case string:
		return t == "true" || t == "1"
	case float64:
		return t != 0
	default:
		return false
	}
}
