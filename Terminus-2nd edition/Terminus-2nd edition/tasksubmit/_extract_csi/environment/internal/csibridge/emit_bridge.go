package csibridge

import "github.com/terminus/snapretctl/internal/volrep"

func SealRetentionReport(scenario, reportPath, danglingPath string) error {
    return volrep.Emit(scenario, reportPath, danglingPath)
}
