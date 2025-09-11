ALTER TABLE student_logs
ALTER COLUMN added_on
SET DEFAULT NOW();


--
DROP FUNCTION IF EXISTS get_shortlisted_universities(bigint);

CREATE OR REPLACE FUNCTION get_shortlisted_universities(p_student_id BIGINT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_agg(
               json_build_object(
                   'id', su.id,
                   'university_id', u.id,
                   'university_name', u.name,
                   'cover_url', u.cover_url,
                   'added_on', to_char(su.added_on, 'YYYY-MM-DD HH24:MI:SS')
               ) ORDER BY su.added_on DESC
           )
    INTO result
    FROM student_shortlisteduniversity su
    JOIN university_university u ON su.university_id = u.id
    WHERE su.student_id = p_student_id;

    RETURN result;

EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'error', 'An unexpected error occurred.'
        );
END;
$$ LANGUAGE plpgsql;


DROP FUNCTION IF EXISTS get_student_full_details(bigint);

CREATE OR REPLACE FUNCTION get_student_full_details(p_student_id BIGINT)
RETURNS JSON AS $$
BEGIN
    RETURN (
        SELECT json_build_object(
        'student', json_build_object(
            'id', s.id,
            'full_name', s.full_name,
            'authToken', s."authToken",
            'email', COALESCE(e.email, ''),
            'mobile_number', COALESCE(pn.mobile_number, '')
        ),
        'student_details', json_build_object(
            'first_name', COALESCE(sd.first_name, ''),
            'last_name', COALESCE(sd.last_name, ''),
            'gender', COALESCE(sd.gender, ''),
            'dob', to_char(sd.dob, 'YYYY-MM-DD'),
            'nationality', COALESCE(sd.nationality, ''),
            'address', COALESCE(sd.address, ''),
            'state', COALESCE(sd.state, ''),
            'city', COALESCE(sd.city, ''),
            'zip_code', COALESCE(sd.zip_code, ''),
            'country', COALESCE(sd.country, '')
        ),
        'education_details', json_build_object(
            'institution_name', COALESCE(ed.institution_name, ''),
            'degree', COALESCE(ed.degree, ''),
            'study_field', COALESCE(ed.study_field, ''),
            'cgpa', ed.cgpa,
            'start_date', to_char(ed.start_date, 'YYYY-MM-DD'),
            'end_date', to_char(ed.end_date, 'YYYY-MM-DD')
        ),
        'experience_details', (
            SELECT json_agg(json_build_object(
                'company_name', ex.company_name,
                'title', ex.title,
                'city', ex.city,
                'country', ex.country,
                'employment_type', ex.employment_type,
                'industry_type', ex.industry_type,
                'start_date', to_char(ex.start_date, 'YYYY-MM-DD'),
                'end_date', CASE WHEN ex.end_date IS NULL THEN NULL ELSE to_char(ex.end_date, 'YYYY-MM-DD') END,
                'currently_working', ex.currently_working
            ) ORDER BY ex.start_date)
            FROM student_experiencedetails ex
            WHERE ex.student_id = s.id
        ),
        'student_logs', (
            SELECT json_agg(json_build_object(
                'logs', l.logs,
                'added_on', to_char(l.added_on, 'YYYY-MM-DD"T"HH24:MI:SS')
            ) ORDER BY l.added_on DESC)
            FROM student_logs l
            WHERE l.student_id = s.id
        ),
        'shortlisted_universities', (
            SELECT json_agg(json_build_object(
                'university_name', u.name,
                'added_on', to_char(su.added_on, 'YYYY-MM-DD"T"HH24:MI:SS')
            ) ORDER BY su.added_on DESC)
            FROM student_shortlisteduniversity su
            JOIN university_university u ON su.university_id = u.id
            WHERE su.student_id = s.id
        ),
        'shortlisted_courses', (
            SELECT json_agg(json_build_object(
                'course_name', c.program_name,
                'university_name', u.name,
                'added_on', to_char(sc.added_on, 'YYYY-MM-DD"T"HH24:MI:SS')
            ) ORDER BY sc.added_on DESC)
            FROM student_shortlistedcourse sc
            JOIN course_course c ON sc.course_id = c.id
            JOIN university_university u ON c.university_id = u.id
            WHERE sc.student_id = s.id
        )
    )
    FROM student_student s
    LEFT JOIN student_email e ON e.student_id = s.id
    LEFT JOIN student_phonenumber pn ON pn.student_id = s.id
    LEFT JOIN student_studentdetails sd ON sd.student_id = s.id
    LEFT JOIN student_educationdetails ed ON ed.student_id = s.id
    WHERE s.id = p_student_id
    );
END;
$$ LANGUAGE plpgsql;


