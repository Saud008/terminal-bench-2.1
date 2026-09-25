package parse

import "fmt"

// ValidateFragment performs light structural checks after parse.
func ValidateFragment(order int, blockType string) error {
	if order < 1 {
		return fmt.Errorf("order must be positive")
	}
	if blockType == "" {
		return fmt.Errorf("block_type required")
	}
	return nil
}
