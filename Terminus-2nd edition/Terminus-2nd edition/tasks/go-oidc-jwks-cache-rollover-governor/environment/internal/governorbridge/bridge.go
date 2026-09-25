package governorbridge

import (
    "github.com/terminus/oidcgov/internal/decide"
    "github.com/terminus/oidcgov/internal/publish"
    "github.com/terminus/oidcgov/internal/hydrate"
    "github.com/terminus/oidcgov/internal/model"
    "github.com/terminus/oidcgov/internal/stagevault"
    "github.com/terminus/oidcgov/internal/timeline"
)

// MaterializeTranscript loads JWKS fixture timelines for offline reconstruction.
func MaterializeTranscript(scenario, fixtureRoot string) (model.TranscriptStage, error) {
    tl, tokens, policy, err := timeline.LoadScenario(scenario, fixtureRoot)
    if err != nil {
        return model.TranscriptStage{}, err
    }
    return model.TranscriptStage{
        Engine:   "oidcgov",
        Scenario: scenario,
        Timeline: tl,
        Tokens:   tokens,
        Policy:   policy,
    }, nil
}

func PersistTranscript(stage model.TranscriptStage) error {
    return stagevault.WriteTranscript("", stage)
}

func RunHydratePass(scenario string) error {
    return hydrate.Run(scenario)
}

func RunDecideBatch(scenario string) error {
    return decide.Run(scenario)
}

func SealGovernanceReport(scenario, outPath string) error {
    return publish.Publish(scenario, outPath)
}
