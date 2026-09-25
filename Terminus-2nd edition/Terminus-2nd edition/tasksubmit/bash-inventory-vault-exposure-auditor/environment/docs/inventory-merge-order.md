# Inventory merge order

hosts.ini sections are recorded in file order as group:kind labels in merge_order.

When expanding group membership, process :children sections before :hosts sections so child groups inherit parent membership before direct host assignment.

Topological expansion: a host in group app with web:children app inherits web group vars after app group vars in precedence order.
