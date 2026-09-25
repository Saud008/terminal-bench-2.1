package topicgate

import (
    "github.com/terminus/kcompactctl/internal/model"
    "github.com/terminus/kcompactctl/internal/coldstore"
    "github.com/terminus/kcompactctl/internal/segpull"
)

func MaterializeTopic(topic, scenario, fixtureRoot string) (model.PartitionStaging, error) {
    records, segCount, err := segpull.LoadTopic(topic, scenario, fixtureRoot)
    if err != nil {
        return model.PartitionStaging{}, err
    }
    return model.PartitionStaging{
        Engine:       "kcompactctl",
        Topic:        topic,
        Scenario:     scenario,
        SegmentCount: segCount,
        RecordCount:  len(records),
        Records:      records,
    }, nil
}

func PersistStaging(snap model.PartitionStaging) error {
    return coldstore.WriteStage("", snap)
}
