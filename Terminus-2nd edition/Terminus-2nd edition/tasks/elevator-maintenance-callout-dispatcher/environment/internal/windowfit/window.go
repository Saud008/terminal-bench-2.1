package windowfit

func WindowAllows(planned, start, end int) bool {
	return planned >= start && planned < end
}

func ShiftAllows(planned, shiftStart, shiftEnd int) bool {
	return planned >= shiftStart && planned <= shiftEnd
}
