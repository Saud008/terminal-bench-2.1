# Fixture catalog

Bundled rootfs trees under /app/fixtures/rootfs/:

| Directory | Focus |
|-----------|--------|
| 001-minimal | Single module, short hook chain |
| 002-firmware-chain | Full hook chain with firmware.map |
| 003-prereq-tiebreak | Equal prerequisites resolved by NN prefix |
| 004-modalias-glob | Wildcard suffix in modules.alias |
| 005-compress-mix | Mixed extensions and compression tags |
| 006-dual-module | Two modules sharing one firmware hook rank |

Hidden verifier fixtures ship under /opt/verifier-fixtures/initramfs/ and are not part of this catalog.
