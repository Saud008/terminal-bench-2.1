package topicgate

import "github.com/terminus/kcompactctl/internal/keysout"

func SealSnapshot(topic, scenario, snapPath, linPath string) error {
    return keysout.Emit(topic, scenario, snapPath, linPath)
}
