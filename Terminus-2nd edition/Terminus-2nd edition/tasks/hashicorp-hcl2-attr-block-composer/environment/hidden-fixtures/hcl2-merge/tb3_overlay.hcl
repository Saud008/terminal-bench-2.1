# second hidden overlay
order 2
block resource aws_instance omega psi
attr tags {"tier":"back","env":"staging"}
merge tags.Name null
