# License priority ranking

When a transmitter record names license_id, bind that grant after verifying matching band_id and geographic containment inside the grant area.

When license_id is empty, multiple license grants may cover the same transmitter site on the same band_id. In that case bind the grant with the highest numeric priority value. Lower numbers lose.
