# Pixel sky linearization

Given pixel coordinates x and y, compute xi equals x minus CRPIX1 and eta equals y minus CRPIX2 using FITS 1-based pixels. Apply the CD matrix to obtain delta RA and delta DEC in degrees, then add CRVAL1 and CRVAL2 respectively.
