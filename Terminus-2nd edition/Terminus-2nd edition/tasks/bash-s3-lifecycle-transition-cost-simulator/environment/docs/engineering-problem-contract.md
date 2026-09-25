# Engineering problem contract — bash-s3-lifecycle-transition-cost-simulator

FinOps charge projection for AWS storage tiers. Core reasoning: calendar-day age drives STANDARD to IA to GLACIER tier moves; Object Lock freezes halt tier moves; unfinished MPU bytes bill separately; delete-marker orphans keep noncurrent revision bytes in the rollup; monthly cost uses actual calendar divisors not flat thirty-day months.
