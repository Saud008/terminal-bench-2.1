# Exposure dependency closure

For each exposure, exposure_refs lists all reachable model unique_ids transitively through depends_on edges where targets are models.

Direct-only listing is insufficient when an exposure depends on a model that itself depends on other models.

Include disabled models in the transitive walk and in exposure_refs. model_order excludes disabled models, but exposure_refs must still list every reachable model unique_id (enabled or disabled).

Sort each exposure_refs list lexicographically.
