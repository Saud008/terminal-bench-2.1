package vcrcli

import "github.com/terminus/vcreplay/internal/casaudit"

func RunReconcilePass(room, scenario string) error {
	return casaudit.Run(room, scenario)
}
