package parse

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"

	"github.com/terminus/casctl/internal/model"
)

func LoadPolicies(path string) ([]model.Policy, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	r := csv.NewReader(f)
	rows, err := r.ReadAll()
	if err != nil {
		return nil, err
	}
	if len(rows) < 2 {
		return nil, fmt.Errorf("empty policy file")
	}
	var out []model.Policy
	for _, row := range rows[1:] {
		if len(row) < 6 {
			continue
		}
		pri, err := strconv.Atoi(row[0])
		if err != nil {
			return nil, err
		}
		out = append(out, model.Policy{
			Priority: pri,
			Sub:      row[1],
			Dom:      row[2],
			Obj:      row[3],
			Act:      row[4],
			Eft:      row[5],
		})
	}
	return out, nil
}

func LoadGroupings(path string) ([]model.Grouping, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	r := csv.NewReader(f)
	rows, err := r.ReadAll()
	if err != nil {
		return nil, err
	}
	if len(rows) < 2 {
		return nil, fmt.Errorf("empty grouping file")
	}
	var out []model.Grouping
	for _, row := range rows[1:] {
		if len(row) < 3 {
			continue
		}
		out = append(out, model.Grouping{
			Child:  row[0],
			Parent: row[1],
			Dom:    row[2],
		})
	}
	return out, nil
}
