package load

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/oasctl/internal/apperr"
	"github.com/terminus/oasctl/internal/model"
)

func OrderPayloads(seed string, payloads []string) []string {
	h := sha256.Sum256([]byte(seed))
	out := append([]string(nil), payloads...)
	for i := len(out) - 1; i > 0; i-- {
		j := int(h[i%len(h)]) % (i + 1)
		out[i], out[j] = out[j], out[i]
	}
	return out
}

func SelectPayloads(seed string, payloads []string) []string {
	if len(payloads) == 0 {
		return nil
	}
	h := sha256.Sum256([]byte(seed))
	bits := int(h[0]) | int(h[1])<<8
	limit := len(payloads)
	if limit > 16 {
		limit = 16
	}
	var selected []string
	for i := 0; i < limit; i++ {
		if (bits>>uint(i))&1 == 1 {
			selected = append(selected, payloads[i])
		}
	}
	if len(selected) == 0 {
		selected = []string{payloads[int(h[2])%len(payloads)]}
	}
	return OrderPayloads(seed, selected)
}

func LoadPayload(path string) (model.PayloadEnvelope, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.PayloadEnvelope{}, fmt.Errorf("%w: %v", apperr.ErrIO, err)
	}
	var env model.PayloadEnvelope
	if err := json.Unmarshal(raw, &env); err != nil {
		return model.PayloadEnvelope{}, fmt.Errorf("%w: %v", apperr.ErrParse, err)
	}
	if env.Operation == "" || env.Data == nil {
		return model.PayloadEnvelope{}, apperr.ErrParse
	}
	return env, nil
}

func LoadPayloadDir(dir string, seed string, names []string) ([]string, []model.PayloadEnvelope, error) {
	selected := SelectPayloads(seed, names)
	files := make([]string, 0, len(selected))
	envs := make([]model.PayloadEnvelope, 0, len(selected))
	for _, name := range selected {
		env, err := LoadPayload(filepath.Join(dir, name))
		if err != nil {
			return nil, nil, fmt.Errorf("%s: %w", name, err)
		}
		files = append(files, name)
		envs = append(envs, env)
	}
	return files, envs, nil
}
