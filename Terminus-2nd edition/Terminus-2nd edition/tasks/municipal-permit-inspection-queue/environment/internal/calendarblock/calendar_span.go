package calendarblock

func DayBlocked(day, startDay, endDay int) bool {
	return day >= startDay && day <= endDay
}
