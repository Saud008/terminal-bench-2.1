package cuewrap

import "fmt"

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
	order := cfg.FieldOrder
	if len(order) == 0 {
		for name := range cfg.Fields {
			order = append(order, name)
		}
	}
	for _, name := range order {
		if _, ok := flat.Fields[name]; !ok {
			unknown = append(unknown, name)
		}
	}
	return unknown
}
