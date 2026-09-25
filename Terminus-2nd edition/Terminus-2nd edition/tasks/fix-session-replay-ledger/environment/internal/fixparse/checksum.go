package fixparse

import (
	"fmt"
	"strconv"
)

// DeclaredBodyLength reads tag 9 from a FIX message.
func DeclaredBodyLength(msg []byte) (int, error) {
	fields := ParseFields(msg)
	raw, ok := fields["9"]
	if !ok {
		return 0, fmt.Errorf("missing tag 9")
	}
	n, err := strconv.Atoi(raw)
	if err != nil {
		return 0, fmt.Errorf("invalid tag 9")
	}
	return n, nil
}

// bodyLengthBeforeChecksum returns the measured span used during ingest validation.
func bodyLengthBeforeChecksum(msg []byte) (int, error) {
	bodyEnd := len(msg)
	for j := 0; j < len(msg); j++ {
		if msg[j] == SOH && j+3 < len(msg) && msg[j+1] == '1' && msg[j+2] == '0' && msg[j+3] == '=' {
			bodyEnd = j
			break
		}
	}
	if bodyEnd == 0 {
		return 0, fmt.Errorf("missing checksum field")
	}
	return bodyEnd, nil
}

func ValidateMessage(msg []byte) error {
	decl, err := DeclaredBodyLength(msg)
	if err != nil {
		return err
	}
	measured, err := bodyLengthBeforeChecksum(msg)
	if err != nil {
		return err
	}
	if decl != measured {
		return fmt.Errorf("body length mismatch: declared %d measured %d", decl, measured)
	}
	fields := ParseFields(msg)
	got, ok := fields["10"]
	if !ok {
		return fmt.Errorf("missing tag 10")
	}
	want, err := ComputeChecksum(msg)
	if err != nil {
		return err
	}
	if got != want {
		return fmt.Errorf("checksum mismatch")
	}
	return nil
}

func ComputeChecksum(msg []byte) (string, error) {
	idx := -1
	for j := 0; j+3 <= len(msg); j++ {
		if msg[j] == '1' && msg[j+1] == '0' && msg[j+2] == '=' {
			idx = j
			break
		}
	}
	if idx < 0 {
		return "", fmt.Errorf("missing checksum field")
	}
	sum := 0
	for _, b := range msg[:idx] {
		sum += int(b)
	}
	return fmt.Sprintf("%03d", sum%256), nil
}
