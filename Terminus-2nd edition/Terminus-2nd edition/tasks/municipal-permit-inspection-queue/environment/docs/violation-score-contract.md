# Violation score contract

Composite score equals base_priority times one hundred plus violation_weight.

Each violation contributes severity multiplied by recency weight. Recency weight is ten minus days_ago for days_ago between one and nine inclusive, ten when days_ago is zero, and one when days_ago is ten or greater.

Higher composite_score ranks earlier in the queue.
