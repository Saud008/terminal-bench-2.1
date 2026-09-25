package icebridge

import "github.com/terminus/iceexpctl/internal/analyzepass"

func RunAnalyzePass(scenario string) error {
    return analyzepass.Run(scenario)
}
