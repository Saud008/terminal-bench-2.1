package receiptfmt

import "fmt"

func PrettyReceipt(merchantID, terminalID, authCode string, amountCents int64) string {
	return fmt.Sprintf("RECEIPT merchant=%s terminal=%s auth=%s amount=%d",
		merchantID, terminalID, authCode, amountCents)
}
