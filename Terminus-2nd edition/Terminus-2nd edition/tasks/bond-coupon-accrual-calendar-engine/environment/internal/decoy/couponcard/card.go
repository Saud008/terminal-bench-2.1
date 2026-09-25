package couponcard

import "fmt"

func PreviewLabel(isin string, couponBPS int) string {
	return fmt.Sprintf("%s coupon %dbps display", isin, couponBPS)
}
