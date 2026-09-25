            # Quantize window policy

            Quantization grid spacing in ticks equals ticks_per_beat divided by the quant divisor with a minimum of one tick. Snap raw note ticks to the nearest grid multiple unless TB3_QUANT_DIVISOR overrides the divisor for a run. A note is grid-consistent when absolute delta between raw and quantized ticks is less than or equal to half the grid spacing. Playtest charts use this grid for lane timing simulation during lane timing validation.
