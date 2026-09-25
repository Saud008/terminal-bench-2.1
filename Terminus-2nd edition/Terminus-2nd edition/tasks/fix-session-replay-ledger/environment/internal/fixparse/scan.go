package fixparse

import (
	"fmt"
	"strconv"

	"github.com/harbor/fix-session-replay-ledger/internal/model"
)

func MessageToExecution(sessionFile string, offset int64, raw []byte) (model.Execution, error) {
	if err := ValidateMessage(raw); err != nil {
		return model.Execution{}, err
	}
	f := ParseFields(raw)
	ex := model.Execution{
		SessionFile: sessionFile,
		FileOffset:  offset,
		ClOrdID:     f["11"],
		ExecID:      f["17"],
		Symbol:      f["55"],
		Side:        f["54"],
		MsgType:     f["35"],
		ExecType:    f["150"],
		SendingTime: f["52"],
		Raw:         append([]byte(nil), raw...),
	}
	if ex.ExecID == "" {
		ex.ExecID = ex.ClOrdID
	}
	if ex.ClOrdID == "" || ex.Symbol == "" || ex.SendingTime == "" {
		return model.Execution{}, fmt.Errorf("missing required tags")
	}
	if v, err := parseFloat(f["32"]); err == nil {
		ex.LastQty = v
	}
	if v, err := parseFloat(f["31"]); err == nil {
		ex.LastPx = v
	}
	if v, err := parseFloat(f["38"]); err == nil {
		ex.OrderQty = v
	}
	return ex, nil
}

func parseFloat(s string) (float64, error) {
	if s == "" {
		return 0, fmt.Errorf("empty")
	}
	return strconv.ParseFloat(s, 64)
}

func ScanSessionFile(sessionFile string, data []byte) ([]model.Execution, error) {
	var out []model.Execution
	msgs := SplitMessages(data)
	offset := int64(0)
	for _, raw := range msgs {
		ex, err := MessageToExecution(sessionFile, offset, raw)
		if err != nil {
			return nil, fmt.Errorf("%s@%d: %w", sessionFile, offset, err)
		}
		out = append(out, ex)
		offset += int64(len(raw))
	}
	return out, nil
}
