package policy

default allow = false

allow { data.foo >= input.threshold }
