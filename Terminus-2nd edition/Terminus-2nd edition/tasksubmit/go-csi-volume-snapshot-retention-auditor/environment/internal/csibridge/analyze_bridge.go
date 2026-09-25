package csibridge

import "github.com/terminus/snapretctl/internal/analyzepass"

func RunAnalyzePass(scenario string) error {
    return analyzepass.Run(scenario)
}
