# AS-path match modes

- origin: last ASN in as_path equals filter.asn
- transit: filter.asn appears in as_path excluding the final origin ASN (path length >= 2)
- exact: as_path equals filter.as_path element-wise
