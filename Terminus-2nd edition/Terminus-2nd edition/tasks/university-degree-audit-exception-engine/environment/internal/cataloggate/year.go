package cataloggate

import "github.com/terminus/degaudit/internal/model"

// EffectiveCatalogYear selects the catalog year governing course eligibility.
func EffectiveCatalogYear(meta model.ScenarioMeta, courses []model.Course) int {
    maxYear := meta.CatalogYear
    for _, c := range courses {
        if c.CatalogYear > maxYear {
            maxYear = c.CatalogYear
        }
    }
    return maxYear
}

func CourseAllowed(course model.Course, catalogYear int) bool {
    return course.CatalogYear <= catalogYear
}
