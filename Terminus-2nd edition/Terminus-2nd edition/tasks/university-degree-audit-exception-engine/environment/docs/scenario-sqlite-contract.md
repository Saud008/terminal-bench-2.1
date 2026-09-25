# SQLite scenario contract

Each scenario directory contains degree.db and meta.json.

Tables:

- scenario_meta(scenario, audit_date, catalog_year, audit_term, catalog_seed)
- students(student_id, display_name)
- courses(course_code, title, credits, catalog_year)
- enrollments(student_id, course_code, term, grade_points, is_transfer)
- transfer_equiv(source_code, target_code, valid_from_year, valid_to_year)
- substitutions(sub_req_id, replaces_req_id, expires_after_term)
- requirements(req_id, parent_req_id, required_credits)
- requirement_courses(req_id, course_code)
- waivers(student_id, req_id, reason)
