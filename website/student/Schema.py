# import decimal
#
# import strawberry
# import typing
#
# @strawberry.type
# class StudentDetailsSchema:
#     first_name: str
#     last_name: str
#     gender: str
#     dob: str
#     nationality: str
#     address: str
#     state: str
#     city: str
#     zip_code: str
#     country: str
#
# @strawberry.type
# class EducationDetailsSchema:
#     institution_name: str
#     degree: str
#     study_field: str
#     cgpa: str
#     start_date: str
#     end_date: str
#
# @strawberry.type
# class ExperienceDetailsSchema:
#     company_name: str
#     title: str
#     city: str
#     country: str
#     employment_type: str
#     industry_type:str
#     start_date: str
#     end_date: str
#     currently_working: str
#
# @strawberry.type
# class TestScoresSchema:
#     exam_type: str
#     english_exam_type: str
#     date: str
#     listening_score:decimal.Decimal
#     reading_score:decimal.Decimal
#     writing_score:decimal.Decimal
#
# class PreferenceSchema:
#     country: str
#     degree: str
#     discipline: str
#     sub_discipline: str
#     date: str
#     budget: int
#
# class ShortlistedUniversity:
#     university_id: int
#     university_name: str
#     added_on: str
#
# class ShortlistedCourseSchema:
#     course_id: int
#     course_name: str
#     added_on: str
#
# class StudentLogsSchema:
#     logs: str
#     added_on: str
#
# class CallRequestSchema:
#     student_id: int
#     student_name: str
#     employee_id: int
#     employee_name: str
#     requested_on: str
#
# class AssignedCounsellor:
#     student_id: int
#     student_name: str
#     employee_id: int
#     employee_name: str
#     assigned_on: str
#
# class AppliedUniversitySchema:
#     course_id: int
#     course_name: str
#     applied_at: str
#     application_number: str
#
#
# @strawberry.type
# class StudentSchema:
#     full_name: str
#     phone_number: str
#     category: str
#     email: str
#     google_file_uuid: str
#     student_details: StudentDetailsSchema
#
#     @classmethod
#     def student