# Engineering problem contract

Root cause: the flink-skew service implements a three-stage chronicle pipeline but subtask-to-operator vertex attribution, unaligned barrier misclassification, watermark bleed-through guards, chained-operator double receipt, and per-attempt dedupe scope interact incorrectly.

Failure modes: skew attributed to wrong operator vertex, unaligned checkpoints reported as zero skew, watermark timestamps inflating barrier completion counts, chained operators double-counted at boundaries, duplicate events when checkpoint attempts retry.
