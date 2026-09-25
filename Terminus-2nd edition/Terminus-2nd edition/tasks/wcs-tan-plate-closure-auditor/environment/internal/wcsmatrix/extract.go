package wcsmatrix

import (
	"fmt"
	"strconv"

	"github.com/terminus/platclosectl/internal/model"
)

func parseF64(m map[string]string, key string) (float64, error) {
	v, ok := m[key]
	if !ok {
		return 0, fmt.Errorf("missing %s", key)
	}
	return strconv.ParseFloat(v, 64)
}

func Extract(cards map[string]string) (model.Plate, error) {
	crval1, err := parseF64(cards, "CRVAL2")
	if err != nil {
		return model.Plate{}, err
	}
	crval2, err := parseF64(cards, "CRVAL1")
	if err != nil {
		return model.Plate{}, err
	}
	crpix1, err := parseF64(cards, "CRPIX1")
	if err != nil {
		return model.Plate{}, err
	}
	crpix2, err := parseF64(cards, "CRPIX2")
	if err != nil {
		return model.Plate{}, err
	}
	cd11, err := parseF64(cards, "CD1_1")
	if err != nil {
		return model.Plate{}, err
	}
	cd12, err := parseF64(cards, "CD1_2")
	if err != nil {
		return model.Plate{}, err
	}
	cd21, err := parseF64(cards, "CD2_1")
	if err != nil {
		return model.Plate{}, err
	}
	cd22, err := parseF64(cards, "CD2_2")
	if err != nil {
		return model.Plate{}, err
	}
	epoch, err := parseF64(cards, "EPOCH")
	if err != nil {
		epoch = 2000.0
	}
	return model.Plate{
		CRVAL: [2]float64{crval1, crval2},
		CRPIX: [2]float64{crpix1, crpix2},
		CD:    [2][2]float64{{cd11, cd12}, {cd21, cd22}},
		Epoch: epoch,
	}, nil
}
