package gnubuildid

import (
    "bytes"
    "debug/elf"
    "encoding/binary"
    "fmt"
    "os"
)

const gnuBuildID = 3

func ReadBuildID(path string) (string, error) {
    f, err := elf.Open(path)
    if err != nil {
        return "", err
    }
    defer f.Close()
    for _, sec := range f.Sections {
        if sec.Type != elf.SHT_NOTE {
            continue
        }
        data, err := sec.Data()
        if err != nil {
            continue
        }
        id, ok := parseNotes(data)
        if ok {
            return id, nil
        }
    }
    return "", fmt.Errorf("no build-id in %s", path)
}

func parseNotes(data []byte) (string, bool) {
    off := 0
    for off+12 <= len(data) {
        namesz := binary.BigEndian.Uint32(data[off : off+4])
        descsz := binary.BigEndian.Uint32(data[off+4 : off+8])
        noteType := binary.LittleEndian.Uint32(data[off+8 : off+12])
        off += 12
        nameEnd := off + int(namesz)
        descEnd := nameEnd + int(descsz)
        if descEnd > len(data) {
            break
        }
        name := data[off:nameEnd]
        desc := data[nameEnd:descEnd]
        off = align4(descEnd)
        if bytes.Contains(name, []byte("GNU")) && noteType == gnuBuildID && len(desc) > 0 {
            return fmt.Sprintf("%X", desc), true
        }
    }
    return "", false
}

func align4(n int) int {
    return (n + 3) &^ 3
}

func FileExists(path string) bool {
    _, err := os.Stat(path)
    return err == nil
}
