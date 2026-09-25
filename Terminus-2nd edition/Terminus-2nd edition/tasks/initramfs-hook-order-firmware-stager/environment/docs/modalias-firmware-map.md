# Modalias and firmware map

Module selection uses three files under etc/irfs/ inside the rootfs:

## modules.load

UTF-8 text, one module name per non-empty line. Lines starting with # are ignored. Order is not significant.

## pci.ids

One modalias string per non-empty line (for example pci:v00001AF4d00001040*). These represent hardware IDs discovered on the target system.

## modules.alias

Located at lib/modules/KVER/modules.alias where KVER is kernel_version from stage.json. Each non-empty line has the form:

```
alias <pattern> <module_name>
```

A module from modules.load is selected only when some alias line targets that module_name and pattern matches at least one pci.ids line. Pattern matching is glob semantics where * matches any suffix.

## firmware.map

Optional file etc/irfs/firmware.map with lines:

```
<module_name> <relative_path_under_lib_firmware>
```

Firmware is included only for modules that passed modalias selection. The staged path is lib/firmware/ plus the relative path. Missing firmware files are skipped silently.
