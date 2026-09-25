#!/usr/bin/env bash
set -euo pipefail
ROOT="/app/projects/demo"
LIBS="${ROOT}/.libs"
INC="${ROOT}/include"
mkdir -p "${ROOT}/install/lib"
gcc -shared -fPIC -I"${INC}" -o "${LIBS}/libmath.so.0.0.0" "${ROOT}/src/libmath.c" -Wl,-soname,libmath.so.0
ln -sf libmath.so.0.0.0 "${LIBS}/libmath.so.0"
ln -sf libmath.so.0 "${LIBS}/libmath.so"
gcc -shared -fPIC -I"${INC}" -o "${LIBS}/libhelper.so.0.0.0" "${ROOT}/src/libhelper.c" \
  "${LIBS}/libmath.so.0" -Wl,-soname,libhelper.so.0 -Wl,-rpath,'$ORIGIN'
ln -sf libhelper.so.0.0.0 "${LIBS}/libhelper.so.0"
ln -sf libhelper.so.0 "${LIBS}/libhelper.so"
gcc -shared -fPIC -I"${INC}" -o "${LIBS}/libutil.so.0.0.0" "${ROOT}/src/libutil.c" \
  "${LIBS}/libmath.so.0" -Wl,-soname,libutil.so.0 -Wl,-rpath,'$ORIGIN'
ln -sf libutil.so.0.0.0 "${LIBS}/libutil.so.0"
ln -sf libutil.so.0 "${LIBS}/libutil.so"
gcc -shared -fPIC -I"${INC}" -o "${LIBS}/libcore.so.0.0.0" "${ROOT}/src/libcore.c" \
  "${LIBS}/libutil.so.0" -Wl,-soname,libcore.so.0 -Wl,-rpath,'$ORIGIN'
ln -sf libcore.so.0.0.0 "${LIBS}/libcore.so.0"
ln -sf libcore.so.0 "${LIBS}/libcore.so"
gcc -c -I"${INC}" -o /tmp/legacy_stub.o "${ROOT}/src/legacy_stub.c"
ar rcs "${LIBS}/liblegacy.a" /tmp/legacy_stub.o
rm -f /tmp/legacy_stub.o
cp -a "${LIBS}/libmath.so"* "${LIBS}/libhelper.so"* "${LIBS}/libutil.so"* "${LIBS}/libcore.so"* "${LIBS}/liblegacy.a" "${ROOT}/install/lib/"
