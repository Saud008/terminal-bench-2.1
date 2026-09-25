package spiffebridge

import "github.com/terminus/spiffectl/internal/normcore"

func RunNormalizePass(scenario string) error {
    return normcore.Run(scenario)
}
