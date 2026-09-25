package chunkbuf

import "bswapd/internal/model"

func StartBlock(sess *model.Session, canon, peer string, seq int) {
	sess.InFlight[canon] = &model.InFlight{Peer: peer, Started: seq}
}

func PartialChunk(sess *model.Session, canon, peer string, bytes int) {
	sess.Partial[canon] = &model.PartialBlock{Peer: peer, Bytes: bytes}
}

func CompleteBlock(sess *model.Session, canon, peer string, bytes int) {
	delete(sess.InFlight, canon)
	delete(sess.Partial, canon)
}

func ClearPartials(sess *model.Session) {
	sess.Partial = map[string]*model.PartialBlock{}
}
