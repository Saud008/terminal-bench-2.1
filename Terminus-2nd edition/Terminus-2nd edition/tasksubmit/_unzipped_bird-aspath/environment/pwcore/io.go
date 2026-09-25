package pwcore

import (
	"encoding/json"
	"os"
)

// LoadPeerInventory loads a peer inventory JSON document for cutover evaluation.
func LoadPeerInventory(path string) (Inventory, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return Inventory{}, err
	}
	var inv Inventory
	if err := json.Unmarshal(raw, &inv); err != nil {
		return Inventory{}, err
	}
	return inv, nil
}

// WriteSealedReport writes the sealed cutover report JSON to path.
func WriteSealedReport(path string, rep Report) error {
	b, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(b, '\n'), 0o644)
}
