package ingest

import (
	"bufio"
	"encoding/json"
	"os"

	"github.com/terminus/modbus-drift-cataloger/internal/model"
)

func LoadFrames(path string) ([]model.Frame, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var frames []model.Frame
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Bytes()
		if len(line) == 0 {
			continue
		}
		var fr model.Frame
		if err := json.Unmarshal(line, &fr); err != nil {
			return nil, err
		}
		frames = append(frames, fr)
	}
	return frames, sc.Err()
}
