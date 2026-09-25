package vcrcli

import (
	"github.com/terminus/vcreplay/internal/model"
	"github.com/terminus/vcreplay/internal/roombind"
	"github.com/terminus/vcreplay/internal/snapfreeze"
)

func MaterializeRoom(room, scenario, fixtureDir string) (model.ChatStaging, error) {
	events, shardCount, err := roombind.LoadRoom(room, scenario, fixtureDir)
	if err != nil {
		return model.ChatStaging{}, err
	}
	return model.ChatStaging{
		Engine:     "vcreplay-v1",
		Room:       room,
		Scenario:   scenario,
		ShardCount: shardCount,
		EventCount: len(events),
		Events:     events,
	}, nil
}

func PersistStaging(snap model.ChatStaging) error {
	return snapfreeze.WriteStage("", snap)
}
