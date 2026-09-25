package graph

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/pulumi-dep-export/internal/model"
)

type DepLedger struct {
	Stack           string              `json:"stack"`
	Epoch           int                 `json:"epoch"`
	AdjacencyDigest string              `json:"adjacency_digest"`
	Resources       []model.Resource    `json:"resources"`
	Adjacency       map[string][]string `json:"adjacency"`
}

func nextEpoch(path string) int {
	prev, err := LoadLedger(path)
	if err != nil || prev.Epoch < 1 {
		return 1
	}
	return prev.Epoch + 1
}

func adjacencyDigest(adj map[string][]string) string {
	keys := make([]string, 0, len(adj))
	for k := range adj {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	canonical := make(map[string][]string, len(keys))
	for _, k := range keys {
		vals := append([]string(nil), adj[k]...)
		sort.Strings(vals)
		canonical[k] = vals
	}
	raw, _ := json.Marshal(canonical)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

func WriteLedger(path string, stack string, resources []model.Resource, adj map[string][]string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	doc := DepLedger{
		Stack:           stack,
		Epoch:           nextEpoch(path),
		AdjacencyDigest: adjacencyDigest(adj),
		Resources:       resources,
		Adjacency:       adj,
	}
	raw, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0o644)
}

func LoadLedger(path string) (DepLedger, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return DepLedger{}, err
	}
	var doc DepLedger
	if err := json.Unmarshal(raw, &doc); err != nil {
		return DepLedger{}, err
	}
	return doc, nil
}
