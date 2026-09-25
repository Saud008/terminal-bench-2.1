package cuewrap

import (
	"fmt"
	"sort"
)

func ValidateClosed(flat FlatSchema, cfg ConfigSpec) error {
	if !flat.Closed {
		return nil
	}
	if unknown := FindUnknownFields(flat, cfg); len(unknown) > 0 {
		return fmt.Errorf("closed schema rejects field %s", unknown[0])
	}
	return nil
}

func FindUnknownFields(flat FlatSchema, cfg ConfigSpec) []string {
	unknown := []string{}
	for name := range cfg.Fields {
		if _, ok := flat.Fields[name]; !ok {
			unknown = append(unknown, name)
		}
	}
	sort.Strings(unknown)
	return unknown
}
