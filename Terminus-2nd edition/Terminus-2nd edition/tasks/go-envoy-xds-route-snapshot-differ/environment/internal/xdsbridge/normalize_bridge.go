package xdsbridge

import "github.com/terminus/xsnapctl/internal/normalizepass"

func RunNormalizePass(scenario string) error {
    return normalizepass.Run(scenario)
}
