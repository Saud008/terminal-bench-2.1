schema Core {
  rev int
}

schema Base {
  embed Core
  flag string
}

schema App {
  embed Base
  mode string
}
