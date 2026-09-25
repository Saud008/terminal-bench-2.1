package export

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/harbor/fix-session-replay-ledger/internal/db"
	"github.com/harbor/fix-session-replay-ledger/internal/model"
	"github.com/harbor/fix-session-replay-ledger/merge"
	"github.com/harbor/fix-session-replay-ledger/pkg/util"
)

func Run(dbPath, outPath string) error {
	store, err := db.Open(dbPath)
	if err != nil {
		return err
	}
	defer store.Close()

	rows, err := store.AllExecutions()
	if err != nil {
		return err
	}

	type symState struct {
		netQty int64
		fills  []model.FillSample
		fillsN int
	}
	bySym := make(map[string]*symState)

	for _, ex := range rows {
		st, ok := bySym[ex.Symbol]
		if !ok {
			st = &symState{}
			bySym[ex.Symbol] = st
		}
		sign := util.SideSign(ex.Side)
		switch ex.ExecType {
		case "1", "2", "F":
			qty := int64(ex.LastQty)
			st.netQty += sign * qty
			st.fills = append(st.fills, model.FillSample{LastQty: ex.LastQty, LastPx: ex.LastPx})
			st.fillsN++
		case "4":
			qty := int64(ex.OrderQty)
			if qty == 0 {
				qty = int64(ex.LastQty)
			}
			st.netQty += sign * qty
		}
	}

	var positions []model.Position
	for sym, st := range bySym {
		vwap := merge.AveragePrice(st.fills)
		positions = append(positions, model.Position{
			Symbol:    sym,
			NetQty:    st.netQty,
			VWAP:      fmt.Sprintf("%.6f", vwap),
			FillCount: st.fillsN,
		})
	}
	sort.Slice(positions, func(i, j int) bool {
		return positions[i].Symbol < positions[j].Symbol
	})

	doc := model.ExportDoc{Version: 1, Positions: positions}
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return err
	}
	b, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(outPath, append(b, '\n'), 0o644); err != nil {
		return err
	}
	fmt.Printf("exported=%d\n", len(positions))
	return nil
}
