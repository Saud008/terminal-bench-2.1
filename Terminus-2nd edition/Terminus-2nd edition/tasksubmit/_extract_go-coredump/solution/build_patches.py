#!/usr/bin/env python3
"""Build solution/patches/*.patch from environment baseline vs oracle fixes."""
from __future__ import annotations

import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
ENV = TASK / "environment"
PATCH_DIR = TASK / "solution" / "patches"
WORK = TASK / "solution" / ".oracle-work"


def write_oracle_tree() -> None:
    import shutil

    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(ENV, WORK)

    fix_gnubuildid(WORK / "internal/gnubuildid/buildid.go")
    fix_vmarange(WORK / "internal/vmarange/locate.go")
    fix_symcatalog(WORK / "internal/symcatalog/catalog.go")
    (WORK / "internal/splitpath/resolve.go").write_text(SPLITPATH_ORACLE, encoding="utf-8")
    (WORK / "internal/crashfold/group.go").write_text(CRASHFOLD_ORACLE, encoding="utf-8")
    fix_frozenstage(WORK / "internal/frozenstage/write.go")
    fix_indexsql(WORK / "internal/indexsql/export.go")
    fix_frame_symbol(WORK / "internal/orchestrate/frame_symbol.go")


def fix_gnubuildid(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    t = t.replace("binary.BigEndian.Uint32(data[off : off+4])", "binary.LittleEndian.Uint32(data[off : off+4])", 1)
    t = t.replace("binary.BigEndian.Uint32(data[off+4 : off+8])", "binary.LittleEndian.Uint32(data[off+4 : off+8])", 1)
    path.write_text(t, encoding="utf-8")


def fix_vmarange(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    t = t.replace("pc <= end", "pc < end")
    old = """func FileRelativeOffset(pcHex string, hit Hit) (uint64, bool) {
    pc, err := parseHex(pcHex)
    if err != nil {
        return 0, false
    }
    if pc < hit.FileOffset {
        return 0, false
    }
    return pc - hit.FileOffset, true
}"""
    new = """func FileRelativeOffset(pcHex string, hit Hit) (uint64, bool) {
    pc, err := parseHex(pcHex)
    if err != nil {
        return 0, false
    }
    start, err := parseHex(hit.Entry.Start)
    if err != nil {
        return 0, false
    }
    if pc < start {
        return 0, false
    }
    return pc - start + hit.FileOffset, true
}"""
    path.write_text(t.replace(old, new), encoding="utf-8")


def fix_symcatalog(path: Path) -> None:
    path.write_text(path.read_text(encoding="utf-8").replace("strings.ToLower", "strings.ToUpper"), encoding="utf-8")


def fix_frozenstage(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    t = t.replace(
        "return rows[i].Timestamp < rows[j].Timestamp",
        "if rows[i].Timestamp != rows[j].Timestamp {\n            return rows[i].Timestamp < rows[j].Timestamp\n        }\n        return rows[i].CrashID < rows[j].CrashID",
    )
    path.write_text(t, encoding="utf-8")


def fix_indexsql(path: Path) -> None:
    t = path.read_text(encoding="utf-8").replace("strings.ToLower(row.BuildID)", "row.BuildID")
    if '"strings"' in t and "strings." not in t.split('"strings"')[1]:
        t = t.replace('\n    "strings"\n', "\n")
    path.write_text(t, encoding="utf-8")


def fix_frame_symbol(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    t = t.replace(
        "splitpath.ResolveSymbol(e, rel, hit.Entry.Path)",
        "splitpath.ResolveSymbol(e, rel, hit.Entry.Path, cat)",
    )
    path.write_text(t, encoding="utf-8")


def make_patches() -> None:
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    rels = [
        "internal/gnubuildid/buildid.go",
        "internal/vmarange/locate.go",
        "internal/symcatalog/catalog.go",
        "internal/splitpath/resolve.go",
        "internal/crashfold/group.go",
        "internal/frozenstage/write.go",
        "internal/indexsql/export.go",
        "internal/orchestrate/frame_symbol.go",
    ]
    for rel in rels:
        out = PATCH_DIR / (rel.replace("/", "__") + ".patch")
        proc = subprocess.run(
            ["diff", "-u", f"internal/{rel.split('internal/',1)[1]}", f"../solution/.oracle-work/{rel}"],
            capture_output=True,
            text=True,
            cwd=ENV,
        )
        if proc.stdout.strip():
            # Normalize headers for patch -p0 under /app
            lines = proc.stdout.splitlines()
            if len(lines) >= 2:
                rel_path = rel  # internal/...
                lines[0] = f"--- {rel_path}"
                lines[1] = f"+++ {rel_path}"
            out.write_text("\n".join(lines) + "\n", encoding="utf-8")


SPLITPATH_ORACLE = '''package splitpath

import (
    "path/filepath"
    "sort"

    "github.com/terminus/coreidx/internal/model"
    "github.com/terminus/coreidx/internal/symcatalog"
)

func ResolveSymbol(entry model.CatalogEntry, fileOffset uint64, mappedPath string, cat *symcatalog.Index) string {
    symbols := entry.Symbols
    if entry.Stripped {
        if entry.DebugPath != "" {
            if alt, ok := cat.LookupPath(entry.DebugPath); ok {
                if sym := lookupNearest(alt.Symbols, fileOffset); sym != "" {
                    return sym
                }
            }
        }
        dbg := filepath.Join(filepath.Dir(mappedPath), ".debug", filepath.Base(mappedPath))
        if alt, ok := cat.LookupPath(dbg); ok {
            if sym := lookupNearest(alt.Symbols, fileOffset); sym != "" {
                return sym
            }
        }
        return lookupNearest(symbols, fileOffset)
    }
    return lookupNearest(symbols, fileOffset)
}

func lookupNearest(symbols []model.SymbolEntry, off uint64) string {
    if len(symbols) == 0 {
        return ""
    }
    sorted := append([]model.SymbolEntry(nil), symbols...)
    sort.Slice(sorted, func(i, j int) bool {
        return sorted[i].Offset < sorted[j].Offset
    })
    best := ""
    for _, s := range sorted {
        if s.Offset <= off {
            best = s.Name
        }
    }
    return best
}
'''

CRASHFOLD_ORACLE = '''package crashfold

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "path/filepath"
    "strings"

    "github.com/terminus/coreidx/internal/model"
)

func GroupKey(rec model.CrashRecord, topPC string, buildID, topSymbol string) string {
    mod := ""
    if len(rec.Threads) > 0 && len(rec.Threads[0].Frames) > 0 {
        mod = filepath.Base(rec.Threads[0].Frames[0].Module)
    }
    h := sha256.New()
    h.Write([]byte(fmt.Sprintf("%s:%d:%s:%s", strings.ToUpper(buildID), rec.Signal, topSymbol, mod)))
    return hex.EncodeToString(h.Sum(nil))
}
'''


if __name__ == "__main__":
    write_oracle_tree()
    make_patches()
    print(f"wrote patches under {PATCH_DIR}")
