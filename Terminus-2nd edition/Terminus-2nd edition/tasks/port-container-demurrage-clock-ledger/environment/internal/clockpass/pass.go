package clockpass

import (
	"encoding/json"
	"os"
)

const passPath = "/app/state/clock-pass.json"

type PassFile struct {
	ClockPass int `json:"clock_pass"`
}

func Reset() error {
	return write(0)
}

func Read() (int, error) {
	data, err := os.ReadFile(passPath)
	if err != nil {
		if os.IsNotExist(err) {
			return 0, nil
		}
		return 0, err
	}
	var pf PassFile
	if err := json.Unmarshal(data, &pf); err != nil {
		return 0, err
	}
	return pf.ClockPass, nil
}

func Increment() error {
	cur, err := Read()
	if err != nil {
		return err
	}
	return write(cur + 1)
}

func write(v int) error {
	body, err := json.Marshal(PassFile{ClockPass: v})
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(passPath, body, 0o644)
}
