package costmin

func rankWalkChoices(choices []WalkChoice) {
    for i := 0; i < len(choices); i++ {
        for j := i + 1; j < len(choices); j++ {
            swap := false
            if choices[i].WalkCostCents > choices[j].WalkCostCents {
                swap = true
            } else if choices[i].WalkCostCents == choices[j].WalkCostCents && choices[i].ToTypeID > choices[j].ToTypeID {
                swap = true
            }
            if swap {
                choices[i], choices[j] = choices[j], choices[i]
            }
        }
    }
}
