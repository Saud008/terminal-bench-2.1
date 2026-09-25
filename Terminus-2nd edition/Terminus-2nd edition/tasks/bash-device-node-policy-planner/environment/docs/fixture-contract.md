# Bundled fixture contract

Paths: /app/fixtures/rules, /app/fixtures/devices.json, /app/fixtures/modalias.tsv, /app/fixtures/policy.json, /app/fixtures/devices-replay-bump.json (ephemeral copy during replay tests)

## Sample device ids

| dev_id | role |
|--------|------|
| disk-a | block disk with serial SN001; matches serial and generic block rules |
| disk-b | block disk without serial override |
| disk-c | block disk with devpath /devices/pci0/0-3/block/sdc used in replay counter bump tests |
| root-hub | USB hub; matches modalias glob rule |

## Expected permission sample

For disk-a after full ingest and export with bundled policy, group is disk and mode is 0660 (four digit octal). Bundled symlink names include disk-generic and disk-by-serial-sn001; collision winner for disk-generic comes from rule file 20-serial.rules.

## Verifier-only coverage

The pytest verifier also uses additional verifier-only assets for extra parent-chain and export coverage. Those assets are not part of the bundled fixture contract above and should not be treated as user-facing examples.
