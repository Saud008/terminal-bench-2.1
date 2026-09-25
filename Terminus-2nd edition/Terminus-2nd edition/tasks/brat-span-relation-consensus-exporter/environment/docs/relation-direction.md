# Relation direction

BRAT relations export as arg1_span and arg2_span. The annotator from field maps to arg1_span and the to field maps to arg2_span without swapping endpoints.

Map annotator-local span ids through namespaced keys of the form annotator:local_id before building consensus relation keys. Do not resolve bare local ids that collide across annotators. Consensus relation keys use doc_id, arg1_span id, arg2_span id, and type after that mapping.
