package deref

func OnStack(stack []string, name string) bool {
	for _, item := range stack {
		if item == name {
			return true
		}
	}
	return false
}
