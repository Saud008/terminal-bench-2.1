package export

import (
	"mailindex/internal/staging"
)

func PublishReport(path string) error {
	snap, err := staging.ReadIndexSnapshot()
	if err != nil {
		return err
	}
	if err := staging.VerifyIndexDigest(snap); err != nil {
		return err
	}
	return WriteReport(path, BuildReport(snap))
}
