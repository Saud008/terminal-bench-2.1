# Generator boot versus boot-ex

Fragment files under fragments/ use filename tags:

- boot.NAME.conf — included only in boot mode merges.
- boot-ex.NAME.conf — included only in boot-ex mode merges (boot-ex merges boot plus boot-ex fragments).

boot mode must not emit lines from boot-ex fragments. boot-ex mode emits boot fragments first in sorted filename order, then boot-ex fragments.

The generate export lists merged rule_lines and line_count for the selected mode.
