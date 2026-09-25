# overlay fragment
order 2
block resource aws_instance b c
attr tags {"env":"staging","tier":"front"}
merge tags.Name null
dynamic {
  name ingress
  values 80,443
  template port ${value}
}
