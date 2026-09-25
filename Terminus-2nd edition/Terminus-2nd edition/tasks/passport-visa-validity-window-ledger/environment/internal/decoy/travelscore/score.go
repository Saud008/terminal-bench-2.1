package travelscore

import "fmt"

func PreviewTravelScore(holderID string, score int) string {
	return fmt.Sprintf("travelscore:%s:%d", holderID, score)
}
