# Bust cancel precedence

ExecType 150=H is a trade bust and applies a signed quantity reversal against the referenced OrigClOrdID execution. Side 1 buy fills add positive qty; side 2 sell fills add negative qty. Bust lines post the opposite signed quantity while leaving the original fill active so net positions return to zero.

ExecTransType 20=1 cancel marks the referenced OrigClOrdID execution inactive. ExecTransType 20=2 correct supersedes an earlier cancel on the same OrigClOrdID when correct sending_time is later: correct rows remain active and restore net qty from LastQty while cancel rows become inactive.

Cancel must not win over a later correct on the same chain,
