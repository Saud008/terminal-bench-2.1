package capture

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/terminus/vicireplay/internal/model"
)

func LoadTrace(path string) (model.Trace, error) {
	f, err := os.Open(path)
	if err != nil {
		return model.Trace{}, err
	}
	defer f.Close()

	var events []model.ViciEvent
	scanner := bufio.NewScanner(f)
	lineNo := 0
	for scanner.Scan() {
		lineNo++
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		var ev model.ViciEvent
		if err := json.Unmarshal([]byte(line), &ev); err != nil {
			return model.Trace{}, fmt.Errorf("line %d: %w", lineNo, err)
		}
		events = append(events, ev)
	}
	if err := scanner.Err(); err != nil {
		return model.Trace{}, err
	}
	if len(events) == 0 {
		return model.Trace{}, fmt.Errorf("empty trace")
	}
	traceID := strings.TrimSuffix(filepathBase(path), filepathExt(path))
	return model.Trace{
		TraceID:   traceID,
		GatewayID: "gw-local",
		Events:    events,
	}, nil
}

func filepathBase(p string) string {
	for i := len(p) - 1; i >= 0; i-- {
		if p[i] == '/' {
			return p[i+1:]
		}
	}
	return p
}

func filepathExt(p string) string {
	base := filepathBase(p)
	for i := len(base) - 1; i >= 0; i-- {
		if base[i] == '.' {
			return base[i:]
		}
	}
	return ""
}
