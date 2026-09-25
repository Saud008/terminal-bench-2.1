#!/usr/bin/env bash
set -euo pipefail

APP="/app"
SRC_PUBLIC="${APP}/fixtures/sources"
SRC_HIDDEN="${APP}/opt-verifier-fixtures/sources"
MAILDIR="${APP}/fixtures/maildir"
HIDDEN="${APP}/opt-verifier-fixtures/maildir"
SEED_PUBLIC="${APP}/fixtures/.maildir-seed"
SEED_HIDDEN="${APP}/opt-verifier-fixtures/.maildir-seed"

install_one() {
  local folder="$1"
  local base="$2"
  local flags="$3"
  local src="$4"
  local mtime="$5"
  local root="$6"
  local name="${base}"
  if [[ -n "${flags}" ]]; then
    name="${base}:2,${flags}"
  fi
  local dest="${root}/${folder}/${name}"
  mkdir -p "${root}/${folder}"
  cp -f "${src}" "${dest}"
  touch -t "${mtime}" "${dest}"
}

rm -rf "${MAILDIR}/cur" "${MAILDIR}/new" "${MAILDIR}/tmp"
rm -rf "${HIDDEN}/cur" "${HIDDEN}/new"
mkdir -p "${MAILDIR}/cur" "${MAILDIR}/new" "${MAILDIR}/tmp"
mkdir -p "${HIDDEN}/cur" "${HIDDEN}/new"

install_one cur "1715500800.1.mail.example.com,S=180" "F" \
  "${SRC_PUBLIC}/root-a-cur.eml" "202505121000.00" "${MAILDIR}"
install_one new "1715508000.3.mail.example.com,S=190" "" \
  "${SRC_PUBLIC}/root-a-new.eml" "202505121230.00" "${MAILDIR}"
install_one cur "1715504400.2.mail.example.com,S=220" "SR" \
  "${SRC_PUBLIC}/reply-a.eml" "202505121100.00" "${MAILDIR}"
install_one cur "1715590800.4.mail.example.com,S=150" "S" \
  "${SRC_PUBLIC}/root-b.eml" "202505130900.00" "${MAILDIR}"
install_one new "1715594400.5.mail.example.com,S=40" "" \
  "${SRC_PUBLIC}/malformed.eml" "202505121400.00" "${MAILDIR}"

install_one cur "1715673600.8.verifier.local,S=180" "S" \
  "${SRC_HIDDEN}/hidden-dup-cur.eml" "202505140700.00" "${HIDDEN}"
install_one cur "1715677200.9.verifier.local,S=200" "R" \
  "${SRC_HIDDEN}/hidden-other.eml" "202505140800.00" "${HIDDEN}"
install_one new "1715680800.10.verifier.local,S=210" "FR" \
  "${SRC_HIDDEN}/hidden-dup-new.eml" "202505140930.00" "${HIDDEN}"

rm -rf "${SEED_PUBLIC}/cur" "${SEED_PUBLIC}/new" "${SEED_HIDDEN}/cur" "${SEED_HIDDEN}/new"
mkdir -p "${SEED_PUBLIC}/cur" "${SEED_PUBLIC}/new" "${SEED_HIDDEN}/cur" "${SEED_HIDDEN}/new"
cp -a "${MAILDIR}/cur/." "${SEED_PUBLIC}/cur/"
cp -a "${MAILDIR}/new/." "${SEED_PUBLIC}/new/"
cp -a "${HIDDEN}/cur/." "${SEED_HIDDEN}/cur/"
cp -a "${HIDDEN}/new/." "${SEED_HIDDEN}/new/"

mkdir -p /opt/verifier-fixtures
rm -rf /opt/verifier-fixtures/maildir
cp -a "${HIDDEN}" /opt/verifier-fixtures/maildir
