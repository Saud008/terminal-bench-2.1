package server

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"github.com/terminus/transit-mock/internal/apperr"
	"github.com/terminus/transit-mock/internal/encrypt"
	"github.com/terminus/transit-mock/internal/model"
	"github.com/terminus/transit-mock/internal/store"
)

type Server struct {
	Store *store.Memory
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/transit/keys/", s.handleKeys)
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})
	return mux
}

func (s *Server) handleKeys(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/v1/transit/keys/")
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) == 0 || parts[0] == "" {
		http.Error(w, "missing key", http.StatusBadRequest)
		return
	}
	name := parts[0]
	if len(parts) == 1 && r.Method == http.MethodGet {
		s.handleGetKey(w, r, name)
		return
	}
	if len(parts) == 2 && parts[1] == "policy" && r.Method == http.MethodGet {
		s.handleGetPolicy(w, r, name)
		return
	}
	if len(parts) == 2 && parts[1] == "config" && r.Method == http.MethodPost {
		s.handleLoadPolicy(w, r, name)
		return
	}
	if len(parts) == 2 && parts[1] == "rotate" && r.Method == http.MethodPost {
		s.handleRotate(w, r, name)
		return
	}
	if len(parts) == 2 && parts[1] == "encrypt" && r.Method == http.MethodPost {
		s.handleEncrypt(w, r, name)
		return
	}
	if len(parts) == 2 && parts[1] == "decrypt" && r.Method == http.MethodPost {
		s.handleDecrypt(w, r, name)
		return
	}
	if len(parts) == 3 && parts[1] == "encrypt" && parts[2] == "batch" && r.Method == http.MethodPost {
		s.handleBatchEncrypt(w, r, name)
		return
	}
	if len(parts) == 3 && parts[1] == "versions" && r.Method == http.MethodDelete {
		ver, err := strconv.Atoi(parts[2])
		if err != nil {
			http.Error(w, "bad version", http.StatusBadRequest)
			return
		}
		s.handleDeleteVersion(w, r, name, ver)
		return
	}
	if len(parts) == 2 && parts[1] == "halt" && r.Method == http.MethodPost {
		s.handleSoftHalt(w, r, name)
		return
	}
	http.Error(w, "not found", http.StatusNotFound)
}

func (s *Server) handleLoadPolicy(w http.ResponseWriter, r *http.Request, name string) {
	var body model.PolicyLoadRequest
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	key, err := s.Store.LoadPolicy(name, body.PolicyFile)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": key})
}

func (s *Server) handleGetKey(w http.ResponseWriter, r *http.Request, name string) {
	key, err := s.Store.Get(name)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": key})
}

func (s *Server) handleGetPolicy(w http.ResponseWriter, r *http.Request, name string) {
	key, err := s.Store.Get(name)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": key.Policy})
}

func (s *Server) handleRotate(w http.ResponseWriter, r *http.Request, name string) {
	key, err := s.Store.Rotate(name)
	if err != nil {
		writeErr(w, err)
		return
	}
	w.Header().Set("X-Vault-Key-Version", strconv.Itoa(key.LatestVersion))
	writeJSON(w, http.StatusOK, map[string]any{"data": key})
}

func (s *Server) handleEncrypt(w http.ResponseWriter, r *http.Request, name string) {
	key, err := s.Store.KeyRef(name)
	if err != nil {
		writeErr(w, err)
		return
	}
	var body model.EncryptRequest
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	cipher, ver, err := encrypt.Encrypt(key, body)
	if err != nil {
		writeErr(w, err)
		return
	}
	w.Header().Set("X-Vault-Key-Version", strconv.Itoa(ver))
	w.Header().Set("X-Vault-Min-Decryption-Version", strconv.Itoa(key.MinDecryptionVersion))
	writeJSON(w, http.StatusOK, map[string]any{"data": map[string]string{"ciphertext": cipher}})
}

func (s *Server) handleDecrypt(w http.ResponseWriter, r *http.Request, name string) {
	key, err := s.Store.KeyRef(name)
	if err != nil {
		writeErr(w, err)
		return
	}
	var body model.DecryptRequest
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	plain, ver, err := encrypt.Decrypt(key, body)
	if err != nil {
		writeErr(w, err)
		return
	}
	w.Header().Set("X-Vault-Key-Version", strconv.Itoa(ver))
	w.Header().Set("X-Vault-Min-Decryption-Version", strconv.Itoa(key.MinDecryptionVersion))
	writeJSON(w, http.StatusOK, map[string]any{"data": map[string]string{"plaintext": plain}})
}

func (s *Server) handleBatchEncrypt(w http.ResponseWriter, r *http.Request, name string) {
	key, err := s.Store.KeyRef(name)
	if err != nil {
		writeErr(w, err)
		return
	}
	var body model.BatchRequest
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	results, minVer, err := encrypt.EncryptBatch(key, body)
	if err != nil {
		writeErr(w, err)
		return
	}
	w.Header().Set("X-Vault-Key-Version", strconv.Itoa(minVer))
	w.Header().Set("X-Vault-Min-Decryption-Version", strconv.Itoa(key.MinDecryptionVersion))
	writeJSON(w, http.StatusOK, map[string]any{"data": model.BatchResponse{BatchResults: results}})
}

func (s *Server) handleDeleteVersion(w http.ResponseWriter, r *http.Request, name string, version int) {
	if err := s.Store.DeleteVersion(name, version); err != nil {
		writeErr(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleSoftHalt(w http.ResponseWriter, r *http.Request, name string) {
	var body struct {
		SoftRotationHaltAfterVersion int `json:"soft_rotation_halt_after_version"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	key, err := s.Store.SetSoftHalt(name, body.SoftRotationHaltAfterVersion)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": key})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func writeErr(w http.ResponseWriter, err error) {
	switch err {
	case apperr.ErrNotFound:
		http.Error(w, err.Error(), http.StatusNotFound)
	case apperr.ErrForbidden:
		http.Error(w, err.Error(), http.StatusForbidden)
	case apperr.ErrRetired:
		w.Header().Set("X-Vault-Halt", "retired")
		http.Error(w, err.Error(), http.StatusForbidden)
	case apperr.ErrBelowMin:
		http.Error(w, err.Error(), http.StatusBadRequest)
	case apperr.ErrInvalidPolicy, apperr.ErrBadRequest:
		http.Error(w, err.Error(), http.StatusBadRequest)
	default:
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
