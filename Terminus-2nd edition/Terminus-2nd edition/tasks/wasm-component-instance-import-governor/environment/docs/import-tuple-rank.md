# Import tuple authenticity rank

Integrity gate for import admission: canonical ordering ranks imports by the ordered pair (module_utf8_bytes, name_utf8_bytes) using lexicographic byte comparison on module first, then name.

Sorting by import name alone is incorrect. Sorting by a single concatenated module-plus-name string without tuple semantics is incorrect.

Example: module "aa" with name "z" ranks before module "b" with name "a" because the module bytes "aa" are lexicographically less than "b".
