# Broadcast rules

Add and Mul use numpy style right aligned broadcasting. Shorter shapes are left padded with ones until ranks match, then each dimension pair must be equal, one, or both symbolic with the same canonical name.
