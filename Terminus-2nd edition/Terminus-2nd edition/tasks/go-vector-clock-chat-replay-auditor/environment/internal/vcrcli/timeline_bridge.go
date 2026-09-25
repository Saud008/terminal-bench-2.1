package vcrcli

import "github.com/terminus/vcreplay/internal/chronicle"

func SealTimeline(room, scenario, output string) error {
	return chronicle.Emit(room, scenario, output)
}
