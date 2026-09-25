package parse

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/terminus/collectdctl/internal/model"
)

var putvalLine = regexp.MustCompile(`^PUTVAL\s+(\S+)(?:\s+interval=(\d+))?\s+(.+)$`)

func ParseStream(content string) ([]model.RawReading, error) {
	var out []model.RawReading
	lines := strings.Split(content, "\n")
	for i, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		r, err := ParseLine(line)
		if err != nil {
			return nil, fmt.Errorf("line %d: %w", i+1, err)
		}
		r.LineNo = i + 1
		out = append(out, r)
	}
	return out, nil
}

func ParseLine(line string) (model.RawReading, error) {
	m := putvalLine.FindStringSubmatch(line)
	if m == nil {
		return model.RawReading{}, fmt.Errorf("bad putval")
	}
	interval := int64(10)
	if m[2] != "" {
		v, err := strconv.ParseInt(m[2], 10, 64)
		if err != nil {
			return model.RawReading{}, fmt.Errorf("bad interval")
		}
		interval = v
	}
	group, err := parseFirstGroup(m[3])
	if err != nil {
		return model.RawReading{}, err
	}
	return model.RawReading{
		Identifier: m[1],
		Interval:   interval,
		Groups:     []model.ValueGroup{group},
	}, nil
}

func parseFirstGroup(rest string) (model.ValueGroup, error) {
	part := strings.Fields(rest)[0]
	fields := strings.Split(part, ":")
	if len(fields) < 2 {
		return model.ValueGroup{}, fmt.Errorf("bad values")
	}
	epoch, err := strconv.ParseInt(fields[0], 10, 64)
	if err != nil {
		return model.ValueGroup{}, fmt.Errorf("bad epoch")
	}
	val, err := strconv.ParseFloat(fields[1], 64)
	if err != nil {
		return model.ValueGroup{}, fmt.Errorf("bad value")
	}
	return model.ValueGroup{Epoch: epoch, Values: []float64{val}}, nil
}
