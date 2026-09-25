package receiptcollapse

func SameDelivery(aRef, bRef, aRecipient, bRecipient string) bool {
	return aRef == bRef && aRecipient == bRecipient
}
