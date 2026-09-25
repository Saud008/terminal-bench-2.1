# PUTVAL text format

Each non-empty, non-comment line:

```text
PUTVAL Identifier [OptionList] Valuelist
```

## Identifier

Unquoted slash path or quoted string (quoted strings may contain `\/`).

Slash layout:

```text
host/plugin[-plugin_instance]/type[-type_instance]
```

## Options

`interval=<seconds>` — default `10` when omitted.

## Valuelist

Space-separated groups. Each group:

```text
epoch:value[:value...]
```

First field is Unix epoch seconds; remaining fields are numeric data-source values.

Example:

```text
PUTVAL rack01/df-root/df_complex interval=10 1704067200:1024:2048
PUTVAL beta/if-eth0/if_octets 1704067200:1000 1704067230:2500
```
