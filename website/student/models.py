from uuid import uuid4

from authentication.models import Employee
from course.models import Course
from django.core.validators import (MaxLengthValidator, MinLengthValidator,
                                    RegexValidator)
from django.db import models
from django.utils import timezone
from university.models import university

# Static variable for country choices using full country names
COUNTRY_CHOICES = [
    ("Afghanistan", "Afghanistan"),
    ("Åland Islands", "Åland Islands"),
    ("Albania", "Albania"),
    ("Algeria", "Algeria"),
    ("American Samoa", "American Samoa"),
    ("AndorrA", "AndorrA"),
    ("Angola", "Angola"),
    ("Anguilla", "Anguilla"),
    ("Antarctica", "Antarctica"),
    ("Antigua and Barbuda", "Antigua and Barbuda"),
    ("Argentina", "Argentina"),
    ("Armenia", "Armenia"),
    ("Aruba", "Aruba"),
    ("Australia", "Australia"),
    ("Austria", "Austria"),
    ("Azerbaijan", "Azerbaijan"),
    ("Bahamas", "Bahamas"),
    ("Bahrain", "Bahrain"),
    ("Bangladesh", "Bangladesh"),
    ("Barbados", "Barbados"),
    ("Belarus", "Belarus"),
    ("Belgium", "Belgium"),
    ("Belize", "Belize"),
    ("Benin", "Benin"),
    ("Bermuda", "Bermuda"),
    ("Bhutan", "Bhutan"),
    ("Bolivia", "Bolivia"),
    ("Bosnia and Herzegovina", "Bosnia and Herzegovina"),
    ("Botswana", "Botswana"),
    ("Bouvet Island", "Bouvet Island"),
    ("Brazil", "Brazil"),
    ("British Indian Ocean Territory", "British Indian Ocean Territory"),
    ("Brunei Darussalam", "Brunei Darussalam"),
    ("Bulgaria", "Bulgaria"),
    ("Burkina Faso", "Burkina Faso"),
    ("Burundi", "Burundi"),
    ("Cambodia", "Cambodia"),
    ("Cameroon", "Cameroon"),
    ("Canada", "Canada"),
    ("Cape Verde", "Cape Verde"),
    ("Cayman Islands", "Cayman Islands"),
    ("Central African Republic", "Central African Republic"),
    ("Chad", "Chad"),
    ("Chile", "Chile"),
    ("China", "China"),
    ("Christmas Island", "Christmas Island"),
    ("Cocos (Keeling) Islands", "Cocos (Keeling) Islands"),
    ("Colombia", "Colombia"),
    ("Comoros", "Comoros"),
    ("Congo", "Congo"),
    ("Congo, The Democratic Republic of the", "Congo, The Democratic Republic of the"),
    ("Cook Islands", "Cook Islands"),
    ("Costa Rica", "Costa Rica"),
    ("Cote D'Ivoire", "Cote D'Ivoire"),
    ("Croatia", "Croatia"),
    ("Cuba", "Cuba"),
    ("Cyprus", "Cyprus"),
    ("Czech Republic", "Czech Republic"),
    ("Denmark", "Denmark"),
    ("Djibouti", "Djibouti"),
    ("Dominica", "Dominica"),
    ("Dominican Republic", "Dominican Republic"),
    ("Ecuador", "Ecuador"),
    ("Egypt", "Egypt"),
    ("El Salvador", "El Salvador"),
    ("Equatorial Guinea", "Equatorial Guinea"),
    ("Eritrea", "Eritrea"),
    ("Estonia", "Estonia"),
    ("Ethiopia", "Ethiopia"),
    ("Falkland Islands (Malvinas)", "Falkland Islands (Malvinas)"),
    ("Faroe Islands", "Faroe Islands"),
    ("Fiji", "Fiji"),
    ("Finland", "Finland"),
    ("France", "France"),
    ("French Guiana", "French Guiana"),
    ("French Polynesia", "French Polynesia"),
    ("French Southern Territories", "French Southern Territories"),
    ("Gabon", "Gabon"),
    ("Gambia", "Gambia"),
    ("Georgia", "Georgia"),
    ("Germany", "Germany"),
    ("Ghana", "Ghana"),
    ("Gibraltar", "Gibraltar"),
    ("Greece", "Greece"),
    ("Greenland", "Greenland"),
    ("Grenada", "Grenada"),
    ("Guadeloupe", "Guadeloupe"),
    ("Guam", "Guam"),
    ("Guatemala", "Guatemala"),
    ("Guernsey", "Guernsey"),
    ("Guinea", "Guinea"),
    ("Guinea-Bissau", "Guinea-Bissau"),
    ("Guyana", "Guyana"),
    ("Haiti", "Haiti"),
    ("Heard Island and Mcdonald Islands", "Heard Island and Mcdonald Islands"),
    ("Holy See (Vatican City State)", "Holy See (Vatican City State)"),
    ("Honduras", "Honduras"),
    ("Hong Kong", "Hong Kong"),
    ("Hungary", "Hungary"),
    ("Iceland", "Iceland"),
    ("India", "India"),
    ("Indonesia", "Indonesia"),
    ("Iran, Islamic Republic Of", "Iran, Islamic Republic Of"),
    ("Iraq", "Iraq"),
    ("Ireland", "Ireland"),
    ("Isle of Man", "Isle of Man"),
    ("Israel", "Israel"),
    ("Italy", "Italy"),
    ("Jamaica", "Jamaica"),
    ("Japan", "Japan"),
    ("Jersey", "Jersey"),
    ("Jordan", "Jordan"),
    ("Kazakhstan", "Kazakhstan"),
    ("Kenya", "Kenya"),
    ("Kiribati", "Kiribati"),
    (
        "Korea, Democratic People'S Republic of",
        "Korea, Democratic People'S Republic of",
    ),
    ("Korea, Republic of", "Korea, Republic of"),
    ("Kuwait", "Kuwait"),
    ("Kyrgyzstan", "Kyrgyzstan"),
    ("Lao People'S Democratic Republic", "Lao People'S Democratic Republic"),
    ("Latvia", "Latvia"),
    ("Lebanon", "Lebanon"),
    ("Lesotho", "Lesotho"),
    ("Liberia", "Liberia"),
    ("Libyan Arab Jamahiriya", "Libyan Arab Jamahiriya"),
    ("Liechtenstein", "Liechtenstein"),
    ("Lithuania", "Lithuania"),
    ("Luxembourg", "Luxembourg"),
    ("Macao", "Macao"),
    (
        "Macedonia, The Former Yugoslav Republic of",
        "Macedonia, The Former Yugoslav Republic of",
    ),
    ("Madagascar", "Madagascar"),
    ("Malawi", "Malawi"),
    ("Malaysia", "Malaysia"),
    ("Maldives", "Maldives"),
    ("Mali", "Mali"),
    ("Malta", "Malta"),
    ("Marshall Islands", "Marshall Islands"),
    ("Martinique", "Martinique"),
    ("Mauritania", "Mauritania"),
    ("Mauritius", "Mauritius"),
    ("Mayotte", "Mayotte"),
    ("Mexico", "Mexico"),
    ("Micronesia, Federated States of", "Micronesia, Federated States of"),
    ("Moldova, Republic of", "Moldova, Republic of"),
    ("Monaco", "Monaco"),
    ("Mongolia", "Mongolia"),
    ("Montserrat", "Montserrat"),
    ("Morocco", "Morocco"),
    ("Mozambique", "Mozambique"),
    ("Myanmar", "Myanmar"),
    ("Namibia", "Namibia"),
    ("Nauru", "Nauru"),
    ("Nepal", "Nepal"),
    ("Netherlands", "Netherlands"),
    ("Netherlands Antilles", "Netherlands Antilles"),
    ("New Caledonia", "New Caledonia"),
    ("New Zealand", "New Zealand"),
    ("Nicaragua", "Nicaragua"),
    ("Niger", "Niger"),
    ("Nigeria", "Nigeria"),
    ("Niue", "Niue"),
    ("Norfolk Island", "Norfolk Island"),
    ("Northern Mariana Islands", "Northern Mariana Islands"),
    ("Norway", "Norway"),
    ("Oman", "Oman"),
    ("Pakistan", "Pakistan"),
    ("Palau", "Palau"),
    ("Palestinian Territory, Occupied", "Palestinian Territory, Occupied"),
    ("Panama", "Panama"),
    ("Papua New Guinea", "Papua New Guinea"),
    ("Paraguay", "Paraguay"),
    ("Peru", "Peru"),
    ("Philippines", "Philippines"),
    ("Pitcairn", "Pitcairn"),
    ("Poland", "Poland"),
    ("Portugal", "Portugal"),
    ("Puerto Rico", "Puerto Rico"),
    ("Qatar", "Qatar"),
    ("Reunion", "Reunion"),
    ("Romania", "Romania"),
    ("Russian Federation", "Russian Federation"),
    ("RWANDA", "RWANDA"),
    ("Saint Helena", "Saint Helena"),
    ("Saint Kitts and Nevis", "Saint Kitts and Nevis"),
    ("Saint Lucia", "Saint Lucia"),
    ("Saint Pierre and Miquelon", "Saint Pierre and Miquelon"),
    ("Saint Vincent and the Grenadines", "Saint Vincent and the Grenadines"),
    ("Samoa", "Samoa"),
    ("San Marino", "San Marino"),
    ("Sao Tome and Principe", "Sao Tome and Principe"),
    ("Saudi Arabia", "Saudi Arabia"),
    ("Senegal", "Senegal"),
    ("Serbia and Montenegro", "Serbia and Montenegro"),
    ("Seychelles", "Seychelles"),
    ("Sierra Leone", "Sierra Leone"),
    ("Singapore", "Singapore"),
    ("Slovakia", "Slovakia"),
    ("Slovenia", "Slovenia"),
    ("Solomon Islands", "Solomon Islands"),
    ("Somalia", "Somalia"),
    ("South Africa", "South Africa"),
    (
        "South Georgia and the South Sandwich Islands",
        "South Georgia and the South Sandwich Islands",
    ),
    ("Spain", "Spain"),
    ("Sri Lanka", "Sri Lanka"),
    ("Sudan", "Sudan"),
    ("Suriname", "Suriname"),
    ("Svalbard and Jan Mayen", "Svalbard and Jan Mayen"),
    ("Swaziland", "Swaziland"),
    ("Sweden", "Sweden"),
    ("Switzerland", "Switzerland"),
    ("Syrian Arab Republic", "Syrian Arab Republic"),
    ("Taiwan, Province of China", "Taiwan, Province of China"),
    ("Tajikistan", "Tajikistan"),
    ("Tanzania, United Republic of", "Tanzania, United Republic of"),
    ("Thailand", "Thailand"),
    ("Timor-Leste", "Timor-Leste"),
    ("Togo", "Togo"),
    ("Tokelau", "Tokelau"),
    ("Tonga", "Tonga"),
    ("Trinidad and Tobago", "Trinidad and Tobago"),
    ("Tunisia", "Tunisia"),
    ("Turkey", "Turkey"),
    ("Turkmenistan", "Turkmenistan"),
    ("Turks and Caicos Islands", "Turks and Caicos Islands"),
    ("Tuvalu", "Tuvalu"),
    ("Uganda", "Uganda"),
    ("Ukraine", "Ukraine"),
    ("United Arab Emirates", "United Arab Emirates"),
    ("United Kingdom", "United Kingdom"),
    ("United States", "United States"),
    ("United States Minor Outlying Islands", "United States Minor Outlying Islands"),
    ("Uruguay", "Uruguay"),
    ("Uzbekistan", "Uzbekistan"),
    ("Vanuatu", "Vanuatu"),
    ("Venezuela", "Venezuela"),
    ("Viet Nam", "Viet Nam"),
    ("Virgin Islands, British", "Virgin Islands, British"),
    ("Virgin Islands, U.S.", "Virgin Islands, U.S."),
    ("Wallis and Futuna", "Wallis and Futuna"),
    ("Western Sahara", "Western Sahara"),
    ("Yemen", "Yemen"),
    ("Zambia", "Zambia"),
    ("Zimbabwe", "Zimbabwe"),
]


class Bucket(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Bucket"
        verbose_name_plural = "Buckets"

    def __str__(self):
        return self.name


phone_regex = RegexValidator(
    regex=r"^\d{10}$", message="Phone number must be exactly 10 digits."
)
otp_regex = RegexValidator(regex=r"^\d{6}$", message="OTP must be exactly 6 digits.")



class Student(models.Model):
    phone_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[phone_regex],
        help_text="Enter a 10-digit phone number.",
    )
    is_otp_verified = models.BooleanField()
    full_name = models.CharField(max_length=200)
    authToken = models.UUIDField(default=uuid4, editable=False, unique=True)
    category = models.ForeignKey(
        Bucket,
        on_delete=models.SET_NULL,
        null=True,
        related_name="students",
    )

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return self.full_name


class Email(models.Model):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="email"
    )
    email = models.EmailField(max_length=150, unique=True)

    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ["email"]

    def __str__(self):
        return self.student.full_name


class OTPRequest(models.Model):
    phone_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[phone_regex],
        help_text="Enter the phone number associated with the OTP.",
    )
    otp = models.CharField(
        max_length=6, validators=[otp_regex], help_text="6-digit OTP code."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_request"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["phone_number"], name="idx_otp_phone")]

    def __str__(self):
        return f"{self.phone_number} - {self.otp}"


class StudentProfilePicture(models.Model):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="profile_picture"
    )
    image_uuid = models.UUIDField(editable=False, unique=True, null=True, blank=True)
    google_file_id = models.CharField(max_length=255, blank=True, default="", null=True)

    def __str__(self):
        return f"{self.student.full_name}'s Profile Picture"

class StudentDetails(models.Model):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="details"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    GENDERS = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    gender = models.CharField(max_length=10, choices=GENDERS)
    dob = models.DateField()
    nationality = models.CharField(max_length=100)
    address = models.CharField(max_length=2000)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=12)
    country = models.CharField(
        max_length=100, choices=COUNTRY_CHOICES
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class EducationDetails(models.Model):
    DEGREE_CHOICES = [
        ("High School", "High School"),
        ("Diploma", "Diploma"),
        ("Associate", "Associate"),
        ("Bachelor", "Bachelor's"),
        ("Master", "Master's"),
        ("MPhil", "M.Phil"),
        ("Doctorate", "Ph.D."),
        ("PostDoc", "Post-Doctorate"),
        ("Certificate", "Certificate"),
        ("Other", "Other"),
    ]

    FIELD_CHOICES = [
        ("Computer Science", "Computer Science"),
        ("Information Technology", "Information Technology"),
        ("Engineering", "Engineering"),
        ("Mathematics", "Mathematics"),
        ("Physics", "Physics"),
        ("Chemistry", "Chemistry"),
        ("Biology", "Biology"),
        ("Business", "Business"),
        ("Economics", "Economics"),
        ("Arts", "Arts"),
        ("Law", "Law"),
        ("Medicine", "Medicine"),
        ("Education", "Education"),
        ("Psychology", "Psychology"),
        ("Social Sciences", "Social Sciences"),
        ("Political Science", "Political Science"),
        ("Architecture", "Architecture"),
        ("Philosophy", "Philosophy"),
        ("Other", "Other"),
    ]

    student = models.OneToOneField(
        "Student", on_delete=models.CASCADE, related_name="education_details"
    )
    institution_name = models.CharField(max_length=255)
    degree = models.CharField(max_length=50, choices=DEGREE_CHOICES)
    study_field = models.CharField(max_length=50, choices=FIELD_CHOICES)
    cgpa = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.institution_name} ({self.degree})"


class ExperienceDetails(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ("Full-time", "Full-time"),
        ("Part-time", "Part-time"),
        ("Internship", "Internship"),
        ("Apprenticeship", "Apprenticeship"),
        ("Contract", "Contract"),
        ("Freelance", "Freelance"),
        ("Self-employed", "Self-employed"),
        ("Temporary", "Temporary"),
        ("Volunteer", "Volunteer"),
        ("Military", "Military"),
        ("Seasonal", "Seasonal"),
        ("Remote", "Remote"),
        ("Other", "Other"),
    ]

    INDUSTRY_TYPE_CHOICES = [
        ("Information Technology", "Information Technology"),
        ("Software Development", "Software Development"),
        ("Internet", "Internet"),
        ("Telecommunications", "Telecommunications"),
        ("Financial Services", "Financial Services"),
        ("Banking", "Banking"),
        ("Insurance", "Insurance"),
        ("Healthcare", "Healthcare"),
        ("Pharmaceuticals", "Pharmaceuticals"),
        ("Education", "Education"),
        ("E-Learning", "E-Learning"),
        ("Government", "Government"),
        ("Defense", "Defense"),
        ("Retail", "Retail"),
        ("E-commerce", "E-commerce"),
        ("Automotive", "Automotive"),
        ("Aerospace", "Aerospace"),
        ("Construction", "Construction"),
        ("Architecture", "Architecture"),
        ("Legal", "Legal"),
        ("Logistics", "Logistics"),
        ("Hospitality", "Hospitality"),
        ("Tourism", "Tourism"),
        ("Marketing", "Marketing"),
        ("Advertising", "Advertising"),
        ("Real Estate", "Real Estate"),
        ("Non-Profit", "Non-Profit"),
        ("Media", "Media"),
        ("Entertainment", "Entertainment"),
        ("Publishing", "Publishing"),
        ("Agriculture", "Agriculture"),
        ("Environmental Services", "Environmental Services"),
        ("Mining", "Mining"),
        ("Oil & Energy", "Oil & Energy"),
        ("Research", "Research"),
        ("Electronics", "Electronics"),
        ("Textiles", "Textiles"),
        ("Manufacturing", "Manufacturing"),
        ("Consumer Goods", "Consumer Goods"),
        ("Consulting", "Consulting"),
        ("Other", "Other"),
    ]

    student = models.ForeignKey(
        "Student", on_delete=models.CASCADE, related_name="experiences"
    )
    company_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(
        max_length=100, choices=COUNTRY_CHOICES
    )  # Updated to use COUNTRY_CHOICES with full names
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_TYPE_CHOICES)
    industry_type = models.CharField(max_length=50, choices=INDUSTRY_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    currently_working = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.company_name} ({self.title})"


class TestScores(models.Model):
    EXAM_TYPE_CHOICES = [
        ("GRE", "GRE"),  # Graduate Record Examinations
        ("GMAT", "GMAT"),  # Graduate Management Admission Test
        ("TOEFL", "TOEFL"),  # Test of English as a Foreign Language
        ("IELTS", "IELTS"),  # International English Language Testing System
        ("SAT", "SAT"),  # Scholastic Assessment Test
        ("ACT", "ACT"),  # American College Testing
        ("LSAT", "LSAT"),  # Law School Admission Test
        ("MCAT", "MCAT"),  # Medical College Admission Test
        ("DAT", "DAT"),  # Dental Admission Test
        ("OAT", "OAT"),  # Optometry Admission Test
        ("PCAT", "PCAT"),  # Pharmacy College Admission Test
        ("MAT", "MAT"),  # Miller Analogies Test
        ("CAT", "CAT"),  # Common Admission Test (India)
        ("GATE", "GATE"),  # Graduate Aptitude Test in Engineering (India)
        ("GMAT-Focus", "GMAT Focus Edition"),  # GMAT Focus Edition
    ]

    ENGLISH_EXAM_CHOICES = [
        ("TOEFL", "TOEFL"),  # Test of English as a Foreign Language
        ("IELTS", "IELTS"),  # International English Language Testing System
        ("PTE", "PTE Academic"),  # Pearson Test of English Academic
        ("Duolingo", "Duolingo English Test"),
        ("CAE", "Cambridge English: Advanced (C1)"),  # Cambridge Advanced English
        ("CPE", "Cambridge English: Proficiency (C2)"),  # Cambridge Proficiency English
        ("OET", "OET"),  # Occupational English Test
        ("TOEIC", "TOEIC"),  # Test of English for International Communication
        ("EFSET", "EF Standard English Test"),  # EF Standard English Test
        ("CELPIP", "CELPIP"),  # Canadian English Language Proficiency Index Program
    ]

    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="test_scores"
    )
    exam_type = models.CharField(
        max_length=50, choices=EXAM_TYPE_CHOICES, help_text="Main aptitude exam"
    )
    english_exam_type = models.CharField(
        max_length=50,
        choices=ENGLISH_EXAM_CHOICES,
        help_text="English proficiency exam",
    )
    date = models.DateField()
    listening_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    reading_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    writing_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = "Test Score"
        verbose_name_plural = "Test Scores"

    def __str__(self):
        return f"{self.exam_type} ({self.date})"


class Preference(models.Model):
    DEGREE_CHOICES = [
        ("High School", "High School"),
        ("Diploma", "Diploma"),
        ("Associate", "Associate"),
        ("Bachelor's", "Bachelor's"),
        ("Master's", "Master's"),
        ("M.Phil", "M.Phil"),
        ("Ph.D.", "Ph.D."),
        ("Post-Doctorate", "Post-Doctorate"),
        ("Certificate", "Certificate"),
        ("Other", "Other"),
    ]

    # Static variable for discipline choices
    DISCIPLINE_CHOICES = [
        ("Computer Science", "Computer Science"),
        ("Information Technology", "Information Technology"),
        ("Engineering", "Engineering"),
        ("Mathematics", "Mathematics"),
        ("Physics", "Physics"),
        ("Chemistry", "Chemistry"),
        ("Biology", "Biology"),
        ("Business", "Business"),
        ("Economics", "Economics"),
        ("Arts", "Arts"),
        ("Law", "Law"),
        ("Medicine", "Medicine"),
        ("Education", "Education"),
        ("Psychology", "Psychology"),
        ("Social Sciences", "Social Sciences"),
        ("Political Science", "Political Science"),
        ("Architecture", "Architecture"),
        ("Philosophy", "Philosophy"),
        ("Other", "Other"),
    ]

    # Static variable for sub-discipline choices (example sub-disciplines per discipline)
    SUB_DISCIPLINE_CHOICES = [
        ("Artificial Intelligence", "Artificial Intelligence"),
        ("Software Engineering", "Software Engineering"),
        ("Civil Engineering", "Civil Engineering"),
        ("Mechanical Engineering", "Mechanical Engineering"),
        ("Pure Mathematics", "Pure Mathematics"),
        ("Applied Physics", "Applied Physics"),
        ("Organic Chemistry", "Organic Chemistry"),
        ("Molecular Biology", "Molecular Biology"),
        ("Finance", "Finance"),
        ("Marketing", "Marketing"),
        ("International Law", "International Law"),
        ("General Medicine", "General Medicine"),
        ("Curriculum Development", "Curriculum Development"),
        ("Clinical Psychology", "Clinical Psychology"),
        ("Sociology", "Sociology"),
        ("International Relations", "International Relations"),
        ("Urban Planning", "Urban Planning"),
        ("Ethics", "Ethics"),
        ("Other", "Other"),
    ]
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="preference"
    )
    country = models.CharField(
        max_length=100, choices=COUNTRY_CHOICES
    )  # Updated to use COUNTRY_CHOICES with full names
    degree = models.CharField(max_length=100, choices=DEGREE_CHOICES)
    discipline = models.CharField(max_length=100, choices=DISCIPLINE_CHOICES)
    sub_discipline = models.CharField(max_length=100, choices=SUB_DISCIPLINE_CHOICES)
    date = models.DateField()
    budget = models.PositiveIntegerField()

    def __str__(self):
        return self.full_name


class ShortlistedUniversity(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="shortlisted_universities"
    )
    university = models.ForeignKey(
        university, on_delete=models.CASCADE, related_name="shortlisted_by_students"
    )
    added_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("student", "university")
        verbose_name = "Shortlisted university"
        verbose_name_plural = "Shortlisted Universities"

    def __str__(self):
        return f"{self.student.full_name} shortlisted {self.university.name}"


class ShortlistedCourse(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="shortlisted_courses"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="shortlisted_by_students"
    )
    added_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("student", "course")
        verbose_name = "Shortlisted Course"
        verbose_name_plural = "Shortlisted Courses"

    def __str__(self):
        return f"{self.student.full_name} shortlisted {self.course.program_name} at {self.course.university.name}"


class StudentLogs(models.Model):
    student = models.ForeignKey(
        "Student",  # safer to use string ref in case Student is defined later
        on_delete=models.CASCADE,
        related_name="StudentLogs",
    )

    logs = models.TextField()
    added_on = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "student_logs"  # custom table name
        ordering = ["-added_on"]  # newest logs first
        verbose_name = "Student Log"
        verbose_name_plural = "Student Logs"

    def __str__(self):
        return (
            f"Log for {self.student} on {self.added_on.strftime('%Y-%m-%d %H:%M:%S')}"
        )


class CallRequest(models.Model):
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="call_requests",
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="call_requests"
    )
    requested_on = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["employee"]),
            models.Index(fields=["requested_on"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "employee"],
                name="unique_student_employee_request",
            )
        ]
        verbose_name = "Call Request"
        verbose_name_plural = "Call Requests"

    def __str__(self):
        return f"Call request: {self.student} → {self.employee} on {self.requested_on:%Y-%m-%d %H:%M}"


class AssignedCounsellor(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="assigned_counsellors",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="counselling_students",
    )
    assigned_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (
            "student",
            "employee",
        )
        verbose_name = "Assigned Counsellor"
        verbose_name_plural = "Assigned Counsellors"
        ordering = ["-assigned_on"]

    def __str__(self):
        return f"{self.employee.name} assigned to {self.student.full_name} on {self.assigned_on:%Y-%m-%d %H:%M}"


# class Application(models.Model):
#     STATUS_CHOICES = [
#         ('draft', 'Draft'),
#         ('submitted', 'Submitted'),
#         ('under_review', 'Under Review'),
#         ('accepted', 'Accepted'),
#         ('rejected', 'Rejected'),
#     ]

#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')
#     university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='applications')
#     status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
#     applied_on = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.student.full_name} → {self.university.name}"


# class DocumentRequirement(models.Model):
#     LEVEL_CHOICES = [
#         ('country', 'Country'),
#         ('university', 'University'),
#         ('student', 'Student'),
#     ]

#     name = models.CharField(max_length=255)
#     doc_type = models.CharField(max_length=100)  # Could reuse Document.DOC_TYPE_CHOICES if needed
#     description = models.TextField(blank=True)
#     level = models.CharField(max_length=20, choices=LEVEL_CHOICES)

#     # Optional links depending on level
#     country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True, related_name='document_requirements')
#     university = models.ForeignKey(University, on_delete=models.CASCADE, null=True, blank=True, related_name='document_requirements')
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='custom_document_requirements')

#     is_mandatory = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         target = self.country or self.university or self.student
#         return f"{self.name} - {self.level} ({target})"


# class Document(models.Model):
#     DOC_TYPE_CHOICES = [
#         ('Passport', 'Passport'),
#         ('Transcript', 'Transcript'),
#         ('Degree Certificate', 'Degree Certificate'),
#         ('Recommendation Letter', 'Recommendation Letter'),
#         ('Statement of Purpose', 'Statement of Purpose'),
#         ('Resume', 'Resume'),
#         ('Test Score Report', 'Test Score Report'),
#         ('ID Proof', 'ID Proof'),
#         ('Other', 'Other'),
#     ]

#     STATUS_CHOICES = [
#         ('uploaded', 'Uploaded'),
#         ('verified', 'Verified'),
#         ('rejected', 'Rejected'),
#         ('in_review', 'In Review'),
#         ('processing', 'Processing'),
#     ]

#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
#     name = models.CharField(max_length=255)
#     doc_type = models.CharField(max_length=100, choices=DOC_TYPE_CHOICES)
#     file_id = models.CharField(max_length=255)
#     status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='uploaded')
#     file_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
#     uploaded_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.name} ({self.doc_type})"

# class DocumentType(models.Model):
#     """Allows adding new document types from admin."""
#     name = models.CharField(max_length=100, unique=True)

#     def __str__(self):
#         return self.name

# class DocumentTemplate(models.Model):
#     """Defines default documents each student should have."""
#     name = models.CharField(max_length=255)
#     doc_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)

#     def __str__(self):
#         return f"{self.name} ({self.doc_type})"


class DocumentTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Document Template"
        verbose_name_plural = "Document Templates"

    def __str__(self):
        return self.name


class TemplateDocument(models.Model):
    template = models.ForeignKey(
        DocumentTemplate, related_name="documents", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    doc_type = models.CharField(
        max_length=100,
        choices=[
            ("Passport", "Passport"),
            ("Transcript", "Transcript"),
            ("Degree Certificate", "Degree Certificate"),
            ("Recommendation Letter", "Recommendation Letter"),
            ("Statement of Purpose", "Statement of Purpose"),
            ("Resume", "Resume"),
            ("Test Score Report", "Test Score Report"),
            ("ID Proof", "ID Proof"),
            ("Marksheet", "Marksheet"),
            ("Other", "Other"),
        ],
    )
    sub_type = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        # unique_together = ("template", "doc_type")
        verbose_name = "Template Document"
        verbose_name_plural = "Template Documents"

    def __str__(self):
        return f"{self.name} ({self.doc_type})"


class StudentDocumentRequirement(models.Model):
    student = models.ForeignKey(
        "student.Student", on_delete=models.CASCADE, related_name="required_documents"
    )
    template_document = models.ForeignKey(
        TemplateDocument, on_delete=models.CASCADE, related_name="student_requirements"
    )

    class Meta:
        unique_together = ("student", "template_document")
        verbose_name = "Student Document Requirement"
        verbose_name_plural = "Student Document Requirements"

    def __str__(self):
        return f"{self.student.full_name} - {self.template_document.name}"


class Document(models.Model):
    DOC_TYPE_CHOICES = [
        ("Passport", "Passport"),
        ("Transcript", "Transcript"),
        ("Degree Certificate", "Degree Certificate"),
        ("Recommendation Letter", "Recommendation Letter"),
        ("Statement of Purpose", "Statement of Purpose"),
        ("Resume", "Resume"),
        ("Test Score Report", "Test Score Report"),
        ("ID Proof", "ID Proof"),
        ("Marksheet", "Marksheet"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("uploaded", "Uploaded"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
        ("in_review", "In Review"),
        ("processing", "Processing"),
    ]

    student = models.ForeignKey(
        "student.Student", on_delete=models.CASCADE, related_name="documents"
    )
    template_document = models.ForeignKey(
        TemplateDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
    )
    name = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=100, choices=DOC_TYPE_CHOICES)
    sub_type = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="uploaded", db_index=True
    )
    file_id = models.CharField(max_length=255)
    file_uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["student", "doc_type"]),
        ]
        unique_together = ("student", "template_document")

    def __str__(self):
        return f"{self.name} ({self.doc_type})"

# from django.db.models.signals import post_save
# from django.dispatch import receiver

# @receiver(post_save, sender=Student)
# def create_default_documents(sender, instance, created, **kwargs):
#     if created:
#         default_docs = [
#             ('ID Proof', 'ID Proof', None),
#             ('10th Marksheet', 'Marksheet', None),
#             ('12th Marksheet', 'Marksheet', None),
#             ('Passport', 'Passport', None)
#         ]

#         for name, doc_type, sub_type in default_docs:
#             Document.objects.create(
#                 student=instance,
#                 name=name,
#                 doc_type=doc_type,
#                 sub_type=sub_type,
#                 status='pending'
#             )


class AppliedUniversity(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    STATUS = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(max_length=55, choices=STATUS, default="pending")
    application_number = models.CharField(max_length=20, unique=True)

    class Meta:
        unique_together = ("student", "course")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.student} → {self.course} ({self.application_number})"
