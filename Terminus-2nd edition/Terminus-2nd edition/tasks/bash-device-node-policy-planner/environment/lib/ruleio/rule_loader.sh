#!/usr/bin/env bash
set -euo pipefail
UDEV_LIB="${UDEV_LIB:-/app/lib}"
# shellcheck source=parse_rules.sh
source "${UDEV_LIB}/ruleio/parse_rules.sh"
# shellcheck source=order_rules.sh
source "${UDEV_LIB}/ruleio/order_rules.sh"

load_ordered_rules() {
  local rules_dir="$1"
  order_rules "$(parse_rules_dir "$rules_dir")"
}
