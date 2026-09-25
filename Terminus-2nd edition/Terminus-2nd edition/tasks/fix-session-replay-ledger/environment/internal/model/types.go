package model

type Execution struct {
	SessionFile string
	FileOffset  int64
	ClOrdID     string
	ExecID      string
	Symbol      string
	Side        string
	LastQty     float64
	LastPx      float64
	OrderQty    float64
	MsgType     string
	ExecType    string
	SendingTime string
	Raw         []byte
}

type StagingMessage struct {
	SessionFile string `json:"session_file"`
	ClOrdID     string `json:"cl_ord_id"`
	ExecID      string `json:"exec_id"`
	Symbol      string `json:"symbol"`
	SendingTime string `json:"sending_time"`
	MsgType     string `json:"msg_type"`
	ExecType    string `json:"exec_type"`
}

type StagingSnapshot struct {
	MessageCount int              `json:"message_count"`
	Messages     []StagingMessage `json:"messages"`
}

type Position struct {
	Symbol    string `json:"symbol"`
	NetQty    int64  `json:"net_qty"`
	VWAP      string `json:"vwap"`
	FillCount int    `json:"fill_count"`
}

type ExportDoc struct {
	Version   int        `json:"version"`
	Positions []Position `json:"positions"`
}

type FillSample struct {
	LastQty float64
	LastPx  float64
}
