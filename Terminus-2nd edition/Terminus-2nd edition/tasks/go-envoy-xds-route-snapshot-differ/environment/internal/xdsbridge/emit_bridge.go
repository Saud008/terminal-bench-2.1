package xdsbridge

import "github.com/terminus/xsnapctl/internal/chgledger"

func SealDiffReport(scenario, outPath string) error {
    return chgledger.Emit(scenario, outPath)
}
