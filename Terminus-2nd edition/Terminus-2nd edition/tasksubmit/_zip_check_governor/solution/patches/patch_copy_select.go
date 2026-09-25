package branchsel

import (
    "sort"

    "github.com/terminus/holdfairctl/internal/model"
)

func copyEligible(c model.ItemCopy, itemID string) bool {
    if c.ItemID != itemID {
        return false
    }
    if c.Status != "available" {
        return false
    }
    return true
}

func branchAllowsTransfer(branchID string, branches map[string]model.Branch) bool {
    b, ok := branches[branchID]
    if !ok {
        return false
    }
    return b.AllowsInterbranchTransfer
}

func orderCandidates(candidates []model.ItemCopy) {
    sort.Slice(candidates, func(i, j int) bool {
        if candidates[i].BranchID != candidates[j].BranchID {
            return candidates[i].BranchID < candidates[j].BranchID
        }
        return candidates[i].CopyID < candidates[j].CopyID
    })
}

func SelectCopy(copies []model.ItemCopy, itemID, pickupBranch string, branches map[string]model.Branch) *model.ItemCopy {
    var candidates []model.ItemCopy
    for _, c := range copies {
        if !copyEligible(c, itemID) {
            continue
        }
        candidates = append(candidates, c)
    }
    if len(candidates) == 0 {
        return nil
    }
    orderCandidates(candidates)
    for _, c := range candidates {
        if c.BranchID == pickupBranch {
            return &c
        }
    }
    for _, c := range candidates {
        if branchAllowsTransfer(c.BranchID, branches) {
            return &c
        }
    }
    return nil
}
