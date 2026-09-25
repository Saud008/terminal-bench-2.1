package model

type CrashRecord struct {
    CrashID   string      `json:"crash_id"`
    Timestamp string      `json:"timestamp"`
    Signal    int         `json:"signal"`
    PID       int         `json:"pid"`
    Threads   []Thread    `json:"threads"`
    Mmap      []MmapEntry `json:"mmap"`
}

type Thread struct {
    Name   string  `json:"name"`
    Frames []Frame `json:"frames"`
}

type Frame struct {
    PC     string `json:"pc"`
    Module string `json:"module"`
}

type MmapEntry struct {
    Start      string `json:"start"`
    End        string `json:"end"`
    Path       string `json:"path"`
    FileOffset string `json:"file_offset"`
}

type Catalog struct {
    Binaries map[string]CatalogEntry `json:"binaries"`
}

type CatalogEntry struct {
    BuildID    string         `json:"build_id"`
    Stripped   bool           `json:"stripped"`
    DebugPath  string         `json:"debug_path,omitempty"`
    Symbols    []SymbolEntry  `json:"symbols"`
}

type SymbolEntry struct {
    Offset uint64 `json:"offset"`
    Name   string `json:"name"`
}

type StagedCrash struct {
    CrashID    string        `json:"crash_id"`
    Timestamp  string        `json:"timestamp"`
    Signal     int           `json:"signal"`
    PID        int           `json:"pid"`
    GroupKey   string        `json:"group_key"`
    BuildID    string        `json:"build_id"`
    TopSymbol  string        `json:"top_symbol"`
    Frames     []ResolvedFrame `json:"frames"`
}

type ResolvedFrame struct {
    PC     string `json:"pc"`
    Module string `json:"module"`
    Symbol string `json:"symbol"`
}

type SummaryGroup struct {
    GroupKey   string `json:"group_key"`
    Signal     int    `json:"signal"`
    BuildID    string `json:"build_id"`
    TopSymbol  string `json:"top_symbol"`
    CrashCount int    `json:"crash_count"`
}

type Summary struct {
    Groups []SummaryGroup `json:"groups"`
    Totals SummaryTotals  `json:"totals"`
}

type SummaryTotals struct {
    GroupCount int `json:"group_count"`
}
