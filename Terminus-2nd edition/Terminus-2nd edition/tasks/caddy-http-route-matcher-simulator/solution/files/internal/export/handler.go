package export

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/caddyroute/internal/staging"
	"github.com/terminus/caddyroute/internal/types"
)

const DefaultExportPath = "/app/output/handler.json"

// ExportHandler writes the handler body for a stable @id.
func ExportHandler(stagePath, handlerID, outPath string) error {
	st, err := staging.Load(stagePath)
	if err != nil {
		return err
	}
	pos, ok := st.HandlerMap[handlerID]
	if !ok {
		return fmt.Errorf("unknown handler id")
	}
	if pos < 0 || pos >= len(st.Routes) {
		return fmt.Errorf("handler map stale")
	}
	row := st.Routes[pos]
	return writeExport(outPath, row.ID, row.HandleJSON)
}

func writeExport(outPath, handlerID, handleJSON string) error {
	var handles []types.Handle
	if err := json.Unmarshal([]byte(handleJSON), &handles); err != nil {
		return err
	}
	payload := types.HandlerExport{
		HandlerID: handlerID,
		Handle:    handles,
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(outPath, data, 0o644)
}
