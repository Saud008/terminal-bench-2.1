schema Base {
  flag string
}

schema Profile {
  embed Base
  closed
  tier disjunct east west
  tag? string
}
