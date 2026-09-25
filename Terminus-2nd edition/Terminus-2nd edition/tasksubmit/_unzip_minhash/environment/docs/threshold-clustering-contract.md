# Threshold clustering contract

Given two MinHash embedding signatures of equal length n, count matching positions where values are equal. The Jaccard similarity eval metric equals matching divided by n as floating point.

Connect two documents with an edge when the estimate is greater than or equal to the jaccard_floor for the group command. Build clusters with union-find over connected components. Each cluster receives a cluster_id formatted c followed by three decimal digits starting at c001 in component discovery order.

Store min_pairwise_estimate as the minimum pairwise estimate among members when cluster size exceeds one, otherwise zero.
