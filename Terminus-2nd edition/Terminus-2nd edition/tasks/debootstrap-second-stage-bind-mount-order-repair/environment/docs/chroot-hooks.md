# Chroot hook contract

Hooks live under {rootfs}/hooks/stage2.d/*.sh and execute only after mount commits complete.

Mount commit sets environment variable S2_COMMITTED=1 before any hook runs. Hooks execute with STAGE2_ROOT pointing at {rootfs}/tree in sorted filename order.

Each hook result records name and exit (integer exit code). Hooks must not run when S2_COMMITTED is unset or zero.

A hook may read marker files under STAGE2_ROOT that prior stages create (for example dev node markers).
