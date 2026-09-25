# Initializer binding

Initializers bind to tensor names in declaration order within the graph document. Sorting initializer names alphabetically is incorrect because downstream value_infos may shadow names depending on ingest order.
