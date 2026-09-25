# coupon-precedence-contract.md

Sort coupons by `precedence` ascending. Split into non-stackable (`stackable = false`) and stackable (`stackable = true`) groups; preserve precedence order within each group.

Discount application on segment subtotal (`base_cents + overage_cents`):

1. **Non-stackable:** compute each coupon’s discount against the **full original subtotal**; apply only the **single largest** discount. `remaining = subtotal - best_discount`.
2. **Stackable:** in precedence order, apply each coupon against the **current remainder** (not the original subtotal). Percent: `remainder * value // 100`. Fixed: `min(value, remainder)`. Subtract each discount from `remaining` (floor at `0`).
3. Total coupon discount = sum of applied discounts, capped at subtotal.

Percent coupons use integer division (`//`). Fixed coupons cannot exceed the base they are applied to.

### Worked example — mixed exclusive + stackable

Subtotal 8200. Coupons: EXCL20 (precedence 1, 20% non-stackable), STACK2 (precedence 2, fixed 300 stackable).

- Best non-stackable: `8200 * 20 // 100 = 1640`; remainder `6560`
- Stackable fixed: `min(300, 6560) = 300`
- Total `coupon_cents = 1940`, `total_cents = 6260`
