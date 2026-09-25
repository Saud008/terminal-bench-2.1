# Pixel to sky projection

FITS pixels are 1-based. With plate solution fields:

- `xi = x_pixel - CRPIX1`
- `eta = y_pixel - CRPIX2`
- `ra = CRVAL1 + CD1_1 * xi + CD1_2 * eta`
- `dec = CRVAL2 + CD2_1 * xi + CD2_2 * eta`

Do not add or subtract an extra one-pixel offset beyond the CRPIX subtraction above.
