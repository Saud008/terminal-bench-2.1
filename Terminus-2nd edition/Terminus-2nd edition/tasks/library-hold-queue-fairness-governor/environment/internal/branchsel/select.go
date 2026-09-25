package branchsel

import (
    "github.com/terminus/holdfairctl/internal/model"
)

func SelectCopy(copies []model.ItemCopy, itemID, pickupBranch string, branches map[string]model.Branch) *model.ItemCopy {
    for i := range copies {
        c := copies[i]
        if c.ItemID != itemID {
            continue
        }
        if c.Status != "available" && c.Status != "on_shelf" {
            continue
        }
        return &c
    }
    return nil
}
