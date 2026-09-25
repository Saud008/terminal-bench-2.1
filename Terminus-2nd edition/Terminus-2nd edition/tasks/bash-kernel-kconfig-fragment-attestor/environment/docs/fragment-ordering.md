# Fragment ordering and override precedence

compile-stage merges layers in this order:

1. defconfig base layer from the bundle root
2. every file matching fragments/*.fragment sorted by basename ascending

Later layers override earlier layers for the same symbol name. Fragment order recorded in stage fragment_order must match basename ascending sort.

Reordering fragments must change final symbol values when fragments conflict.
