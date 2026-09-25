#!/usr/bin/env bash

check_release_policy() {
  # qid class seed — broken baseline always allows
  POLICY_OK=1
  return 0
}

compute_policy_digest() {
  POLICY_DIGEST=""
}
