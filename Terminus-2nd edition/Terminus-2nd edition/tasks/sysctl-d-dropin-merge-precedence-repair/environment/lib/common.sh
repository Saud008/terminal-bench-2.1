#!/usr/bin/env bash

die() {
  echo "sysctlmerge: $*" >&2
  exit "${2:-1}"
}
