package model

import "time"

type Transition struct {
	At       time.Time
	OffsetSec int
}

type TimeZone struct {
	TZID         string
	Transitions  []Transition
}

type Event struct {
	UID      string
	DTStart  time.Time
	Floating bool
	TZID     string
	RRule    RRule
	EXDates  []time.Time
	RDates   []time.Time
}

type RRule struct {
	Freq     string
	Interval int
	ByDay    []string
	BySetPos int
	Count    int
	Until    *time.Time
	UntilUTC bool
}

type Occurrence struct {
	UID       string
	StartUTC  time.Time
}
