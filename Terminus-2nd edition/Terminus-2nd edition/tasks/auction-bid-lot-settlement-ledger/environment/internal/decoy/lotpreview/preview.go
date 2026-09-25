package lotpreview

import "fmt"

func PreviewLot(lotID, title string) string {
    return fmt.Sprintf("preview:%s:%s", lotID, title)
}
