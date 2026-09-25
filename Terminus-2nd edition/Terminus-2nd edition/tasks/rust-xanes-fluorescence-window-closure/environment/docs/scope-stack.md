# Scope stack

Traverse the window tree in DFS preorder. Push each node's `edge_code` on enter and pop on leave, including nodes whose `channels` list is empty.

An `edge_code` beginning with `?` is an undeclared edge marker and must yield `status=error` with exit code 1.
