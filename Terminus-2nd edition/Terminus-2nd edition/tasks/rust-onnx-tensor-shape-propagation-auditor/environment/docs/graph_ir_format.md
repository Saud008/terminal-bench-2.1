# Graph IR format

Each graph is a JSON document under the graph directory. Files are processed in lexicographic path order. A graph exposes graph_id, optional symbol_links pairs, inputs with optional default_shape, initializers, nodes, and value_infos.

Inputs and initializers carry shape arrays mixing integer literals and symbolic strings. Symbol names are case sensitive. The integer -1 in an input shape marks a dynamic placeholder that must be replaced from default_shape before propagation begins.
