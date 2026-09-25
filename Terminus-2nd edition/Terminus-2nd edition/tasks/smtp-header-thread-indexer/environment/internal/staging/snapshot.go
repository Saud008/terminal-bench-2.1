package staging

import "mailindex/internal/model"

func WriteIndexSnapshot(_ string, _ model.Report) error {
	return nil
}

func ReadIndexSnapshot() (model.IndexSnapshot, error) {
	return model.IndexSnapshot{}, errMissingSnapshot
}

var errMissingSnapshot = missingSnapshotError{}

type missingSnapshotError struct{}

func (missingSnapshotError) Error() string {
	return "index snapshot missing"
}
