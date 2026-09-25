package walcommit

import (
    "encoding/json"
    "os"
    "sort"

    "github.com/terminus/qqraftctl/internal/model"
    "github.com/terminus/qqraftctl/internal/workpad"
)

func ExportLedger(st model.Staging, ledgerPath, sealPath string) error {
    var rows []model.ExportRow
    for qid, msgs := range st.QueueStates {
        rows = append(rows, model.ExportRow{
            QueueID: qid, Messages: msgs, LeaderID: st.LeaderID,
            Term: st.CurrentTerm, CommitIndex: st.CommitIndex,
            Replicas: append([]string(nil), st.Membership...),
        })
    }
    sort.Slice(rows, func(i, j int) bool {
        if rows[i].Term != rows[j].Term {
            return rows[i].Term > rows[j].Term
        }
        return rows[i].QueueID < rows[j].QueueID
    })
    f, err := os.Create(ledgerPath)
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
    seal := model.LedgerSeal{
        RaftSeal:        workpad.ComputeRaftSeal(st),
        MembershipEpoch: st.CurrentTerm,
        ExportRowCount:  len(rows),
    }
    raw, err := json.MarshalIndent(seal, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(sealPath, append(raw, '\n'), 0o644)
}
