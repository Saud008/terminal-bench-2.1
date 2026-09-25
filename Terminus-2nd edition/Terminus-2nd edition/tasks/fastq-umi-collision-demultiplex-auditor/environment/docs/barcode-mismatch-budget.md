# Barcode mismatch budget

Sample assignment during lumidmx demux run compares the R1 extracted barcode against effective lane sample barcodes.

Hamming distance is computed position-wise over the barcode_length window. Positions where either the observed or expected base is N are ignored and do not increment the distance.

A pair matches a sample when distance is less than or equal to mismatch_budget from the manifest. When multiple samples qualify, the sample with the lowest distance wins.

Effective barcodes come from lane-manifest-precedence.md before mismatch counting.
