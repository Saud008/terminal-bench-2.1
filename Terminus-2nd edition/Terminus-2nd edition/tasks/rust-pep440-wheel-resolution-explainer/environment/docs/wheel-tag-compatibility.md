# Wheel tag compatibility

Wheel tags use the form cp{py}-abi-platform. A wheel whose abi segment is abi3 is compatible with any CPython version at or above the cp tag python level on the same platform family.

Select the first lexicographically sorted compatible tag when multiple wheels match.
