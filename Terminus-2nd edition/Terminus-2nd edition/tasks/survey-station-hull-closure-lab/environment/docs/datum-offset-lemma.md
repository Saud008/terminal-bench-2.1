# Residual vector lemma

For every input vertex [lon, lat], the residual vertex is
[lon - datum_offset.lon, lat - datum_offset.lat].

Datum offsets come from /app/config/stationclos.json. Residual subtraction must not add the
datum components.
