package log

import (
	"bufio"
	"encoding/json"
	"os"
	"strings"

	"dnsmasqledger/internal/model"
)

func LoadReplay(path string) ([]model.ReplayEvent, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var events []model.ReplayEvent
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		var ev model.ReplayEvent
		if err := json.Unmarshal([]byte(line), &ev); err != nil {
			return nil, err
		}
		events = append(events, ev)
	}
	return events, sc.Err()
}
