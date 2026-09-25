#!/usr/bin/env bash

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

sha1_file() {
  sha1sum "$1" | awk '{print $1}'
}
