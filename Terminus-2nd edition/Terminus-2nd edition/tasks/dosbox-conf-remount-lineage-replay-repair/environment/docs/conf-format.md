# Conf format

DOSBox-style INI fragments used by `dosbox-plan`.

## Sections

- `[config]` — remap directives (`remap_drive OLD NEW`)
- `[autoexec]` — startup commands (`mount`, `imgmount`)

Section headers are case-insensitive. Unknown sections are ignored.

## Comments

`#` starts an end-of-line comment. Blank lines are ignored.

## Line continuation

A line ending with `\` continues on the next physical line. The backslash and surrounding whitespace on the continued line are removed when joining.

Example:

```ini
[autoexec]
mount C /data/long/\
folder/game
```

parses as `mount C /data/long/folder/game`.

## Commands

### remap_drive

```
remap_drive D E
```

### mount / imgmount

```
mount C /host/path
imgmount D /images/disc.iso -t iso
```

Drive token is the first argument (optional trailing `:` allowed). Additional imgmount flags are ignored for lineage path extraction (second token is the path).

## Manifest

Each fixture directory contains `manifest.txt`:

```
# profile default
game.conf
extra.conf
```

Lines name conf files relative to the fixture directory. Profiles are selected by `--profile`; only the `default` profile is used in bundled fixtures (manifest has no profile headers — all listed files belong to `default`).
