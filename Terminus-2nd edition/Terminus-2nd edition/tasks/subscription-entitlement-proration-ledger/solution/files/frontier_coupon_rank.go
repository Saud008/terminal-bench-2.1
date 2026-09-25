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
    sort.Slice(coupons, func(i, j int) bool { return coupons[i].Precedence < coupons[j].Precedence })
    var nonStack, stack []Coupon
    for _, c := range coupons {
        if c.Stackable {
            stack = append(stack, c)
        } else {
            nonStack = append(nonStack, c)
        }
    }
    var discount int64
    remaining := subtotal
    if len(nonStack) > 0 {
        var best int64
        for _, c := range nonStack {
            d := couponAmount(subtotal, c)
            if d > best {
                best = d
            }
        }
        discount += best
        remaining = subtotal - best
    }
    for _, c := range stack {
        d := couponAmount(remaining, c)
        discount += d
        remaining -= d
        if remaining < 0 {
            remaining = 0
        }
    }
    if discount > subtotal {
        return subtotal
    }
    return discount
}

func couponAmount(base int64, c Coupon) int64 {
    switch c.Kind {
    case "percent":
        return base * c.Value / 100
    case "fixed":
        if c.Value > base {
            return base
        }
        return c.Value
    default:
        return 0
    }
}
