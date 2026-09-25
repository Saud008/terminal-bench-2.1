import json
import struct
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/verifier-fixtures/coreidx_hidden")

def build_elf(path, build_id_hex):
    path.parent.mkdir(parents=True, exist_ok=True)
    build_id = bytes.fromhex(build_id_hex)
    note_name = b"GNU\x00"
    note_desc = build_id
    namesz, descsz = len(note_name), len(note_desc)
    note_hdr = struct.pack("<III", namesz, descsz, 3)
    note_body = note_hdr + note_name + b"\x00" * ((4 - (namesz % 4)) % 4)
    note_body += note_desc + b"\x00" * ((4 - (descsz % 4)) % 4)
    note_off = 0x200
    e_ident = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 8
    elf_hdr = struct.pack("<16sHHIQQQIHHHHHH", e_ident, 2, 0x3E, 1, 0x401000, 64, 0x300, 0, 64, 56, 1, 64, 3, 2)
    phdr = struct.pack("<IIQQQQQQ", 4, 4, note_off, 0x600000, 0x600000, len(note_body), len(note_body), 4)
    buf = bytearray(b"\x00" * 0x400)
    buf[0:64] = elf_hdr
    buf[64:120] = phdr
    buf[note_off:note_off+len(note_body)] = note_body
    path.write_bytes(bytes(buf))

svc = ROOT / "binaries" / "svc"
build_elf(svc, "deadbeef00000001")
cat = {
    "binaries": {
        str(svc): {
            "build_id": "DEADBEEF00000001",
            "stripped": False,
            "symbols": [{"offset": 0x500, "name": "svc.handle"}],
        }
    }
}
(ROOT / "catalog").mkdir(parents=True, exist_ok=True)
(ROOT / "catalog" / "build_index.json").write_text(json.dumps(cat, indent=2) + "\n")
crash = {
    "crash_id": "c-hidden-delta",
    "timestamp": "2026-04-01T08:00:00Z",
    "signal": 11,
    "pid": 9001,
    "threads": [{"name": "main", "frames": [{"pc": "0x400500", "module": "svc"}]}],
    "mmap": [{"start": "0x400000", "end": "0x401000", "path": str(svc), "file_offset": "0x0"}],
}
(ROOT / "crashes").mkdir(parents=True, exist_ok=True)
(ROOT / "crashes" / "hidden.crash.jsonl").write_text(json.dumps(crash) + "\n")
print("hidden ok", ROOT)
