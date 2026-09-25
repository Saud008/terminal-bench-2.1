# Operator shape rules

MatMul supports batched ranks. For ranks greater than two, leading dimensions must broadcast like numpy while the trailing matrix multiply uses inner axis agreement.

Reshape target arrays may include one -1 entry. That entry must become total elements divided by the product of the other target dimensions.

Concat sums sizes on the declared axis when symbolic names unify.
