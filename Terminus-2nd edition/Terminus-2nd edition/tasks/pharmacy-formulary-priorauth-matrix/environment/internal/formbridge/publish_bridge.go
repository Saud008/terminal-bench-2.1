package formbridge

import "github.com/terminus/formulatrix/internal/matrixout"

func SealMatrixPublish(scenario, outPath string) error {
    return matrixout.Emit(scenario, outPath)
}
