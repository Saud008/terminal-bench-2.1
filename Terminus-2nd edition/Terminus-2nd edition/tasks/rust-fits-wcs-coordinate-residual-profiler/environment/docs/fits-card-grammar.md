# FITS card grammar

Header files use one simplified FITS card per line. Columns 1 through 8 hold the keyword left justified. An equals sign separates the keyword from the value field. String values may be wrapped in single quotes; parsers must strip surrounding quotes before numeric conversion. CONTINUE cards are not used in bundled fixtures.
