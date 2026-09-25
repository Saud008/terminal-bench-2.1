package dispatchorchestrator

import (
	"encoding/json"
	"os"

	"github.com/terminus/calloutd/internal/faultpriority"
	"github.com/terminus/calloutd/internal/rosterfeed"
	"github.com/terminus/calloutd/internal/rosterbind"
	"github.com/terminus/calloutd/internal/calloutpublish"
)

func LoadRoster(scenario, fixtureDir string) error {
	b, err := rosterfeed.LoadBundle(scenario, fixtureDir)
	if err != nil {
		return err
	}
	return rosterfeed.PersistBundle(b)
}

func RankFaults(scenario string) error {
	if err := rosterfeed.BundleLoaded(scenario); err != nil {
		return err
	}
	return faultpriority.RunScoring()
}

func BindRoster(scenario string) error {
	if err := rosterfeed.BundleLoaded(scenario); err != nil {
		return err
	}
	return rosterbind.RunAssignment()
}

func EmitCallout(scenario, outPath string) error {
	if err := rosterfeed.BundleLoaded(scenario); err != nil {
		return err
	}
	return calloutpublish.PublishRoster(scenario, outPath)
}

func BumpPublishPass() error {
	path := "/app/state/callout-pass.json"
	var body struct {
		CalloutPass int `json:"callout_pass"`
		PublishPass  int `json:"publish_pass"`
	}
	raw, _ := os.ReadFile(path)
	_ = json.Unmarshal(raw, &body)
	body.PublishPass++
	out, err := json.Marshal(body)
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}
