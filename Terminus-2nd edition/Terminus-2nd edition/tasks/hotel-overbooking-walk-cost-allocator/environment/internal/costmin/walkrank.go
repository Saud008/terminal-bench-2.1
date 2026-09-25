package costmin

func rankWalkChoices(choices []WalkChoice) {
    for i := 0; i < len(choices); i++ {
        for j := i + 1; j < len(choices); j++ {
            if choices[i].WalkCostCents < choices[j].WalkCostCents {
                choices[i], choices[j] = choices[j], choices[i]
            } else if choices[i].WalkCostCents == choices[j].WalkCostCents && choices[i].ToTypeID < choices[j].ToTypeID {
                choices[i], choices[j] = choices[j], choices[i]
            }
        }
    }
}
