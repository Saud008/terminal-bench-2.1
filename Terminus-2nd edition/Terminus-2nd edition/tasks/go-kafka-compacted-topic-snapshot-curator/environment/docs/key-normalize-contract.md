# Key canonicalization

Keys are trimmed of leading and trailing whitespace.

NFC normalization is applied to the UTF-8 decoded string; sequences that do not compose under NFC are left in their decoded form and are considered already canonical.

Keys with user: prefix lower-case the prefix and following username segment only; other prefixes are unchanged aside from trim and NFC.
