package replayledger

import (
    "encoding/json"
    "os"

    "github.com/terminus/wfhistctl/internal/model"
)

func WriteRiskReport(path string, rows []model.RiskRow) error {
    f, err := os.Create(path)
    if err != nil {
        return err
    }
    defer f.Close()
    for _, row := range rows {
        line, err := json.Marshal(row)
        if err != nil {
            return err
        }
        if _, err := f.Write(append(line, '\n')); err != nil {
            return err
        }
    }
    return nil
}

func SealAllowsExport(seal model.CompactionSeal) bool {
    return seal.CompactionSeal > 0
}
