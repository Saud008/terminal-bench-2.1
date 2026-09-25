package model

type MailMessage struct {
	MessageID   string
	DateUnix    int64
	Subject     string
	InReplyTo   string
	References  []string
	SourceFile  string
	FileOrder   int
	MessageIndex int
}

type Stats struct {
	FilesRead                int
	MessagesIn               int
	MessagesIndexed          int
	MessagesSkippedMalformed int
	MessagesDeduped          int
	ThreadsResolved          int
}

type IndexedMessage struct {
	MessageID    string `json:"message_id"`
	ThreadRootID string `json:"thread_root_id"`
	DateUnix     int64  `json:"date_unix"`
	Subject      string `json:"subject"`
	IsRoot       bool   `json:"is_root"`
}

type Report struct {
	IndexVersion             int              `json:"index_version"`
	FilesRead                int              `json:"files_read"`
	MessagesIn               int              `json:"messages_in"`
	MessagesIndexed          int              `json:"messages_indexed"`
	MessagesSkippedMalformed int              `json:"messages_skipped_malformed"`
	MessagesDeduped          int              `json:"messages_deduped"`
	ThreadsResolved          int              `json:"threads_resolved"`
	MessagesIndexedList      []IndexedMessage `json:"messages_indexed_list"`
}

type IndexSnapshot struct {
	Version                  int    `json:"version"`
	ThreadDB                 string `json:"thread_db"`
	IndexDigest              string `json:"index_digest"`
	IndexVersion             int    `json:"index_version"`
	FilesRead                int              `json:"files_read"`
	MessagesIn               int              `json:"messages_in"`
	MessagesIndexed          int              `json:"messages_indexed"`
	MessagesSkippedMalformed int              `json:"messages_skipped_malformed"`
	MessagesDeduped          int              `json:"messages_deduped"`
	ThreadsResolved          int              `json:"threads_resolved"`
	MessagesIndexedList      []IndexedMessage `json:"messages_indexed_list"`
}

func ReportFromSnapshot(s IndexSnapshot) Report {
	return Report{
		IndexVersion:             s.IndexVersion,
		FilesRead:                s.FilesRead,
		MessagesIn:               s.MessagesIn,
		MessagesIndexed:          s.MessagesIndexed,
		MessagesSkippedMalformed: s.MessagesSkippedMalformed,
		MessagesDeduped:          s.MessagesDeduped,
		ThreadsResolved:          s.ThreadsResolved,
		MessagesIndexedList:      s.MessagesIndexedList,
	}
}

func SnapshotFromReport(threadDB string, report Report) IndexSnapshot {
	return IndexSnapshot{
		Version:                  1,
		ThreadDB:                 threadDB,
		IndexDigest:              "",
		IndexVersion:             report.IndexVersion,
		FilesRead:                report.FilesRead,
		MessagesIn:               report.MessagesIn,
		MessagesIndexed:          report.MessagesIndexed,
		MessagesSkippedMalformed: report.MessagesSkippedMalformed,
		MessagesDeduped:          report.MessagesDeduped,
		ThreadsResolved:          report.ThreadsResolved,
		MessagesIndexedList:      report.MessagesIndexedList,
	}
}
