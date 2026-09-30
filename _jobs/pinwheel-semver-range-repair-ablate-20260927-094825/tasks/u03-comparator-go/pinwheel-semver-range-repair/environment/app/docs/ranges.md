# Versions and ranges

Ranges in `pin.json` and in registry dependencies are written the way npm
users write them, and pinwheel has to agree with npm about what they mean.
The reference is the `semver` package, version 7.x, used with its defaults:
strict parsing (`loose: false`) and `includePrerelease: false`. Where this
page is silent, `semver` 7.x decides.

## Versions

A version is SemVer 2.0.0: `MAJOR.MINOR.PATCH`, then optionally `-` and a
prerelease, then optionally `+` and build metadata.

- MAJOR, MINOR and PATCH are non-negative integers without leading zeros.
- Prerelease and build metadata are dot-separated identifiers made of
  `[0-9A-Za-z-]`, none of them empty. A prerelease identifier made only of
  digits is numeric and must not have leading zeros; build identifiers may.
- One leading `v` is accepted and dropped (`v1.2.3` is `1.2.3`). Nothing
  else may precede the version.

### Precedence

Versions are ordered by SemVer 2.0.0 section 11:

1. MAJOR, MINOR, PATCH compared numerically, in that order.
2. A version with a prerelease is lower than the same version without one.
3. Two prereleases are compared identifier by identifier, left to right:
   numeric identifiers numerically, other identifiers by ASCII order, and a
   numeric identifier is always lower than a non-numeric one. If all
   identifiers of the shorter prerelease are equal to the start of the longer
   one, the longer one is higher.

Build metadata is ignored: `1.0.0+a` and `1.0.0+b` have equal precedence,
and `1.0.0+a` satisfies `=1.0.0`.

## Ranges

```
range-set  := range ( "||" range )*
range      := hyphen | simple ( " " simple )* | ""
hyphen     := partial " - " partial
simple     := primitive | partial | tilde | caret
primitive  := ( "<" | ">" | ">=" | "<=" | "=" ) partial
tilde      := ( "~" | "~>" ) partial
caret      := "^" partial
partial    := xr ( "." xr ( "." xr qualifier? )? )?
xr         := "x" | "X" | "*" | numeric
```

Whitespace around `||` is optional. Whitespace between an operator and its
version is allowed (`>= 1.2.3`). The empty range means `*`.

A version satisfies a range-set if it satisfies at least one of the `||`
alternatives, and it satisfies an alternative if it satisfies every
comparator in it (subject to the prerelease rule below).

Missing fields and `x`/`X`/`*` are wildcards. Each form reduces to plain
comparators:

| form | meaning |
|------|---------|
| `*`, `""` | any version |
| `1`, `1.x` | `>=1.0.0 <2.0.0-0` |
| `1.2`, `1.2.x` | `>=1.2.0 <1.3.0-0` |
| `1.2.3`, `=1.2.3` | exactly 1.2.3 |
| `>1` | `>=2.0.0` |
| `>1.2` | `>=1.3.0` |
| `>=1.2` | `>=1.2.0` |
| `<1.2` | `<1.2.0-0` |
| `<=1.2` | `<1.3.0-0` |
| `<*`, `>*` | nothing |
| `~1.2.3` | `>=1.2.3 <1.3.0-0` |
| `~1.2` | `>=1.2.0 <1.3.0-0` |
| `~1` | `>=1.0.0 <2.0.0-0` |
| `~0.2.3` | `>=0.2.3 <0.3.0-0` |
| `~1.2.3-beta.2` | `>=1.2.3-beta.2 <1.3.0-0` |
| `^1.2.3` | `>=1.2.3 <2.0.0-0` |
| `^0.2.3` | `>=0.2.3 <0.3.0-0` |
| `^0.0.3` | `>=0.0.3 <0.0.4-0` |
| `^1.2` | `>=1.2.0 <2.0.0-0` |
| `^0.2` | `>=0.2.0 <0.3.0-0` |
| `^0.0` | `>=0.0.0 <0.1.0-0` |
| `^1`, `^0` | `>=1.0.0 <2.0.0-0`, `>=0.0.0 <1.0.0-0` |
| `^1.2.3-beta.2` | `>=1.2.3-beta.2 <2.0.0-0` |
| `1.2.3 - 2.3.4` | `>=1.2.3 <=2.3.4` |
| `1.2 - 2.3.4` | `>=1.2.0 <=2.3.4` |
| `1.2.3 - 2.3` | `>=1.2.3 <2.4.0-0` |
| `1.2.3 - 2` | `>=1.2.3 <3.0.0-0` |

A caret allows changes that do not modify the left-most non-zero field of
the version it is given.

## Prereleases

A prerelease version only satisfies an alternative when, in addition to
meeting every comparator, the alternative contains a comparator whose
version is itself a prerelease with the same MAJOR.MINOR.PATCH. So
`1.2.3-alpha.7` satisfies `>1.2.3-alpha.3`, but `3.4.5-alpha.9` does not,
even though it is greater than `1.2.3-alpha.3`.
