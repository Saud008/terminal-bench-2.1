package cuewrap

import "fmt"

func ValidateEvalSnapshot(snap *EvalSnapshot) error {
	if snap == nil {
		return fmt.Errorf("eval snapshot is nil")
	}
	if !snap.OK {
		if len(snap.Values) > 0 {
			return fmt.Errorf("failed eval snapshot must not include values")
		}
		return nil
	}
	if len(snap.Values) == 0 {
		return fmt.Errorf("successful eval snapshot missing values")
	}
	for path := range snap.Values {
		if len(path) < 7 || path[:7] != "config." {
			return fmt.Errorf("eval snapshot value path %q must start with config.", path)
		}
	}
	return nil
}
