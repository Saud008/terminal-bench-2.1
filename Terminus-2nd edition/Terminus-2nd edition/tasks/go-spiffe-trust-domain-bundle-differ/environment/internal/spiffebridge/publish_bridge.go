package spiffebridge

import "github.com/terminus/spiffectl/internal/diffseal"

func SealAtlasReport(scenario, outPath string) error {
    return diffseal.Publish(scenario, outPath)
}
