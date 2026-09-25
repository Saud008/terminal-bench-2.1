package archive

import (
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"os"

	"github.com/terminus/asynq-archive-repair/internal/model"
)

func GzipWrapClose(w *gzip.Writer) error {
	if err := w.Flush(); err != nil {
		return err
	}
	return w.Close()
}

type MemberWriter struct {
	file   *os.File
	gz     *gzip.Writer
	idx    *IndexBuilder
	offset int64
	start  int64
	ids    []string
}

func NewMemberWriter(bundle *os.File, idx *IndexBuilder, offset int64) (*MemberWriter, error) {
	gz := gzip.NewWriter(bundle)
	return &MemberWriter{
		file:   bundle,
		gz:     gz,
		idx:    idx,
		offset: offset,
		start:  offset,
	}, nil
}

func (m *MemberWriter) WriteTask(t model.TaskRecord) error {
	raw, err := json.Marshal(t)
	if err != nil {
		return err
	}
	if _, err := io.WriteString(m.gz, string(raw)+"\n"); err != nil {
		return err
	}
	m.ids = append(m.ids, t.ID)
	m.offset, err = m.file.Seek(0, io.SeekCurrent)
	return err
}

func (m *MemberWriter) CloseMember(partial bool) error {
	if partial {
		return m.gz.Close()
	}
	if err := m.gz.Close(); err != nil {
		return err
	}
	end, err := m.file.Seek(0, io.SeekCurrent)
	if err != nil {
		return err
	}
	size := end - m.start
	m.idx.AddMember(m.start, size, m.ids)
	m.offset = end
	return nil
}

type IndexBuilder struct {
	idx model.IndexFile
}

func NewIndexBuilder() *IndexBuilder {
	return &IndexBuilder{idx: model.IndexFile{Version: 1}}
}

func (b *IndexBuilder) AddMember(offset, size int64, ids []string) {
	mid := len(b.idx.Members)
	b.idx.Members = append(b.idx.Members, model.MemberIndex{
		MemberID:       mid,
		FileOffset:     offset,
		CompressedSize: size,
		TaskIDs:        append([]string(nil), ids...),
	})
	for line, id := range ids {
		b.idx.Tasks = append(b.idx.Tasks, model.TaskLoc{ID: id, MemberID: mid, Line: line})
	}
}

func (b *IndexBuilder) AddPartial(offset, size int64, ids []string) {}

func (b *IndexBuilder) Build() model.IndexFile {
	return b.idx
}

func WriteIndex(path string, idx model.IndexFile) error {
	raw, err := json.MarshalIndent(idx, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal index: %w", err)
	}
	return os.WriteFile(path, raw, 0o644)
}

func ReadIndex(path string) (model.IndexFile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.IndexFile{}, err
	}
	var idx model.IndexFile
	if err := json.Unmarshal(raw, &idx); err != nil {
		return model.IndexFile{}, err
	}
	return idx, nil
}

func ReadMemberTasks(bundlePath string, member model.MemberIndex) ([]model.TaskRecord, error) {
	f, err := os.Open(bundlePath)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	if _, err := f.Seek(member.FileOffset, io.SeekStart); err != nil {
		return nil, err
	}
	lim := io.LimitReader(f, member.CompressedSize)
	gz, err := gzip.NewReader(lim)
	if err != nil {
		return nil, err
	}
	defer gz.Close()
	dec := json.NewDecoder(gz)
	var out []model.TaskRecord
	for {
		var t model.TaskRecord
		if err := dec.Decode(&t); err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}
		out = append(out, t)
	}
	return out, nil
}
