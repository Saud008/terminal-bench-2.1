schema NodeA {
  embed NodeB
  a int
}

schema NodeB {
  embed NodeA
  b int
}
