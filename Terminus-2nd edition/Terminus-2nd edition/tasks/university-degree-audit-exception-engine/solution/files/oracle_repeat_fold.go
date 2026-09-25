package repeatfold

import "github.com/terminus/degaudit/internal/model"

type FoldedCourse struct {
    CourseCode  string
    GradePoints float64
    Credits     float64
}

func FoldEnrollments(enrolls []model.Enrollment, courses map[string]model.Course) []FoldedCourse {
    seen := map[string]FoldedCourse{}
    for _, e := range enrolls {
        c, ok := courses[e.CourseCode]
        if !ok {
            continue
        }
        if prev, exists := seen[e.CourseCode]; !exists || e.GradePoints > prev.GradePoints {
            seen[e.CourseCode] = FoldedCourse{
                CourseCode:  e.CourseCode,
                GradePoints: e.GradePoints,
                Credits:     c.Credits,
            }
        }
    }
    out := make([]FoldedCourse, 0, len(seen))
    for _, fc := range seen {
        out = append(out, fc)
    }
    return out
}
