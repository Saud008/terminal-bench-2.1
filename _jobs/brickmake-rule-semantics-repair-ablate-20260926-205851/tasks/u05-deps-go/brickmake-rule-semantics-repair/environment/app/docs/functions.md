# Functions

`$(name arguments)` or `${name arguments}` calls a function when `name` is
one of the names below followed by a blank. Arguments are separated by
commas that are not inside parentheses (or braces) of the same kind as the
call; the last argument takes any remaining commas.

## Text

| Call | Result |
|---|---|
| `$(subst from,to,text)` | every `from` replaced by `to` |
| `$(patsubst pattern,replacement,text)` | words matching `pattern` replaced; `%` in `replacement` is the stem |
| `$(strip text)` | words separated by single spaces |
| `$(findstring find,text)` | `find` if it occurs in `text`, else empty |
| `$(filter patterns,text)` / `$(filter-out patterns,text)` | words that match / do not match any pattern |
| `$(sort list)` | sorted, duplicates removed |
| `$(word n,text)` | the n-th word (n >= 1) |
| `$(wordlist s,e,text)` | words s to e |
| `$(words text)`, `$(firstword text)`, `$(lastword text)` | |

## File names

| Call | Result |
|---|---|
| `$(dir names)` | directory part of each word, `./` if none |
| `$(notdir names)` | file part of each word |
| `$(suffix names)` | suffix of each word that has one |
| `$(basename names)` | each word without its suffix |
| `$(addsuffix s,names)`, `$(addprefix p,names)` | |
| `$(join list1,list2)` | word-by-word concatenation |
| `$(wildcard patterns)` | existing files matching each pattern, each pattern's matches sorted |

## Control and introspection

| Call | Result |
|---|---|
| `$(if cond,then[,else])` | `then` if `cond` (stripped, then expanded) is not empty; only the chosen branch is expanded |
| `$(or a,b,...)` | first non-empty argument |
| `$(and a,b,...)` | last argument if all are non-empty, else empty |
| `$(foreach var,list,text)` | `text` expanded once per word with `var` bound to it |
| `$(call name,arg1,...)` | expands variable `name` with `$(1)`, `$(2)`, ... bound; `$(0)` is `name` |
| `$(origin name)`, `$(flavor name)`, `$(value name)` | see `variables.md` |
| `$(shell command)` | standard output of `/bin/sh -c command`, newlines turned into spaces |
| `$(info text)` | prints `text` on stdout |
| `$(warning text)` | prints `FILE:LINE: text` on stderr |
| `$(error text)` | stops with `FILE:LINE: *** text.  Stop.` |

Messages raised while a recursive variable is expanded report the position
of that variable's definition.
