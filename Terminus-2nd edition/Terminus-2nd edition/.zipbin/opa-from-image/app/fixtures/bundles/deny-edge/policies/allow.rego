package policy

default allow = false

allow { input.threshold > 100 }
