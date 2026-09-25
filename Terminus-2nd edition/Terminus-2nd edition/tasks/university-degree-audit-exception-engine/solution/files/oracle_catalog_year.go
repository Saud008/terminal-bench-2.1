package cataloggate

import "github.com/terminus/degaudit/internal/model"

func EffectiveCatalogYear(meta model.ScenarioMeta, courses []model.Course) int {
    return meta.CatalogYear
}

func CourseAllowed(course model.Course, catalogYear int) bool {
    return course.CatalogYear <= catalogYear
}
