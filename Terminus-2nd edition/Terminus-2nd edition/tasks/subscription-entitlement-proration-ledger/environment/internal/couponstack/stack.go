package couponstack

import "sort"

type Coupon struct {
    CouponID   string
    Precedence int
    Kind       string
    Value      int64
    Stackable  bool
}

func ApplyCoupons(subtotal int64, coupons []Coupon) int64 {
    if subtotal <= 0 || len(coupons) == 0 {
        return 0
    }
    sort.Slice(coupons, func(i, j int) bool {
        return coupons[i].Precedence < coupons[j].Precedence
    })
    var discount int64
    for _, c := range coupons {
        var d int64
        switch c.Kind {
        case "percent":
            d = subtotal * c.Value / 100
        case "fixed":
            d = c.Value
        default:
            continue
        }
        if d > subtotal {
            d = subtotal
        }
        discount += d
    }
    return discount
}
