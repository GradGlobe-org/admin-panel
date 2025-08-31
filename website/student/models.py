from uuid import uuid4
from django.db import models
from django.utils import timezone
from university.models import university
from course.models import Course



# Static variable for country choices using full country names
COUNTRY_CHOICES = [
    ('Afghanistan', 'Afghanistan'),
    ('Åland Islands', 'Åland Islands'),
    ('Albania', 'Albania'),
    ('Algeria', 'Algeria'),
    ('American Samoa', 'American Samoa'),
    ('AndorrA', 'AndorrA'),
    ('Angola', 'Angola'),
    ('Anguilla', 'Anguilla'),
    ('Antarctica', 'Antarctica'),
    ('Antigua and Barbuda', 'Antigua and Barbuda'),
    ('Argentina', 'Argentina'),
    ('Armenia', 'Armenia'),
    ('Aruba', 'Aruba'),
    ('Australia', 'Australia'),
    ('Austria', 'Austria'),
    ('Azerbaijan', 'Azerbaijan'),
    ('Bahamas', 'Bahamas'),
    ('Bahrain', 'Bahrain'),
    ('Bangladesh', 'Bangladesh'),
    ('Barbados', 'Barbados'),
    ('Belarus', 'Belarus'),
    ('Belgium', 'Belgium'),
    ('Belize', 'Belize'),
    ('Benin', 'Benin'),
    ('Bermuda', 'Bermuda'),
    ('Bhutan', 'Bhutan'),
    ('Bolivia', 'Bolivia'),
    ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'),
    ('Botswana', 'Botswana'),
    ('Bouvet Island', 'Bouvet Island'),
    ('Brazil', 'Brazil'),
    ('British Indian Ocean Territory', 'British Indian Ocean Territory'),
    ('Brunei Darussalam', 'Brunei Darussalam'),
    ('Bulgaria', 'Bulgaria'),
    ('Burkina Faso', 'Burkina Faso'),
    ('Burundi', 'Burundi'),
    ('Cambodia', 'Cambodia'),
    ('Cameroon', 'Cameroon'),
    ('Canada', 'Canada'),
    ('Cape Verde', 'Cape Verde'),
    ('Cayman Islands', 'Cayman Islands'),
    ('Central African Republic', 'Central African Republic'),
    ('Chad', 'Chad'),
    ('Chile', 'Chile'),
    ('China', 'China'),
    ('Christmas Island', 'Christmas Island'),
    ('Cocos (Keeling) Islands', 'Cocos (Keeling) Islands'),
    ('Colombia', 'Colombia'),
    ('Comoros', 'Comoros'),
    ('Congo', 'Congo'),
    ('Congo, The Democratic Republic of the', 'Congo, The Democratic Republic of the'),
    ('Cook Islands', 'Cook Islands'),
    ('Costa Rica', 'Costa Rica'),
    ('Cote D\'Ivoire', 'Cote D\'Ivoire'),
    ('Croatia', 'Croatia'),
    ('Cuba', 'Cuba'),
    ('Cyprus', 'Cyprus'),
    ('Czech Republic', 'Czech Republic'),
    ('Denmark', 'Denmark'),
    ('Djibouti', 'Djibouti'),
    ('Dominica', 'Dominica'),
    ('Dominican Republic', 'Dominican Republic'),
    ('Ecuador', 'Ecuador'),
    ('Egypt', 'Egypt'),
    ('El Salvador', 'El Salvador'),
    ('Equatorial Guinea', 'Equatorial Guinea'),
    ('Eritrea', 'Eritrea'),
    ('Estonia', 'Estonia'),
    ('Ethiopia', 'Ethiopia'),
    ('Falkland Islands (Malvinas)', 'Falkland Islands (Malvinas)'),
    ('Faroe Islands', 'Faroe Islands'),
    ('Fiji', 'Fiji'),
    ('Finland', 'Finland'),
    ('France', 'France'),
    ('French Guiana', 'French Guiana'),
    ('French Polynesia', 'French Polynesia'),
    ('French Southern Territories', 'French Southern Territories'),
    ('Gabon', 'Gabon'),
    ('Gambia', 'Gambia'),
    ('Georgia', 'Georgia'),
    ('Germany', 'Germany'),
    ('Ghana', 'Ghana'),
    ('Gibraltar', 'Gibraltar'),
    ('Greece', 'Greece'),
    ('Greenland', 'Greenland'),
    ('Grenada', 'Grenada'),
    ('Guadeloupe', 'Guadeloupe'),
    ('Guam', 'Guam'),
    ('Guatemala', 'Guatemala'),
    ('Guernsey', 'Guernsey'),
    ('Guinea', 'Guinea'),
    ('Guinea-Bissau', 'Guinea-Bissau'),
    ('Guyana', 'Guyana'),
    ('Haiti', 'Haiti'),
    ('Heard Island and Mcdonald Islands', 'Heard Island and Mcdonald Islands'),
    ('Holy See (Vatican City State)', 'Holy See (Vatican City State)'),
    ('Honduras', 'Honduras'),
    ('Hong Kong', 'Hong Kong'),
    ('Hungary', 'Hungary'),
    ('Iceland', 'Iceland'),
    ('India', 'India'),
    ('Indonesia', 'Indonesia'),
    ('Iran, Islamic Republic Of', 'Iran, Islamic Republic Of'),
    ('Iraq', 'Iraq'),
    ('Ireland', 'Ireland'),
    ('Isle of Man', 'Isle of Man'),
    ('Israel', 'Israel'),
    ('Italy', 'Italy'),
    ('Jamaica', 'Jamaica'),
    ('Japan', 'Japan'),
    ('Jersey', 'Jersey'),
    ('Jordan', 'Jordan'),
    ('Kazakhstan', 'Kazakhstan'),
    ('Kenya', 'Kenya'),
    ('Kiribati', 'Kiribati'),
    ('Korea, Democratic People\'S Republic of', 'Korea, Democratic People\'S Republic of'),
    ('Korea, Republic of', 'Korea, Republic of'),
    ('Kuwait', 'Kuwait'),
    ('Kyrgyzstan', 'Kyrgyzstan'),
    ('Lao People\'S Democratic Republic', 'Lao People\'S Democratic Republic'),
    ('Latvia', 'Latvia'),
    ('Lebanon', 'Lebanon'),
    ('Lesotho', 'Lesotho'),
    ('Liberia', 'Liberia'),
    ('Libyan Arab Jamahiriya', 'Libyan Arab Jamahiriya'),
    ('Liechtenstein', 'Liechtenstein'),
    ('Lithuania', 'Lithuania'),
    ('Luxembourg', 'Luxembourg'),
    ('Macao', 'Macao'),
    ('Macedonia, The Former Yugoslav Republic of', 'Macedonia, The Former Yugoslav Republic of'),
    ('Madagascar', 'Madagascar'),
    ('Malawi', 'Malawi'),
    ('Malaysia', 'Malaysia'),
    ('Maldives', 'Maldives'),
    ('Mali', 'Mali'),
    ('Malta', 'Malta'),
    ('Marshall Islands', 'Marshall Islands'),
    ('Martinique', 'Martinique'),
    ('Mauritania', 'Mauritania'),
    ('Mauritius', 'Mauritius'),
    ('Mayotte', 'Mayotte'),
    ('Mexico', 'Mexico'),
    ('Micronesia, Federated States of', 'Micronesia, Federated States of'),
    ('Moldova, Republic of', 'Moldova, Republic of'),
    ('Monaco', 'Monaco'),
    ('Mongolia', 'Mongolia'),
    ('Montserrat', 'Montserrat'),
    ('Morocco', 'Morocco'),
    ('Mozambique', 'Mozambique'),
    ('Myanmar', 'Myanmar'),
    ('Namibia', 'Namibia'),
    ('Nauru', 'Nauru'),
    ('Nepal', 'Nepal'),
    ('Netherlands', 'Netherlands'),
    ('Netherlands Antilles', 'Netherlands Antilles'),
    ('New Caledonia', 'New Caledonia'),
    ('New Zealand', 'New Zealand'),
    ('Nicaragua', 'Nicaragua'),
    ('Niger', 'Niger'),
    ('Nigeria', 'Nigeria'),
    ('Niue', 'Niue'),
    ('Norfolk Island', 'Norfolk Island'),
    ('Northern Mariana Islands', 'Northern Mariana Islands'),
    ('Norway', 'Norway'),
    ('Oman', 'Oman'),
    ('Pakistan', 'Pakistan'),
    ('Palau', 'Palau'),
    ('Palestinian Territory, Occupied', 'Palestinian Territory, Occupied'),
    ('Panama', 'Panama'),
    ('Papua New Guinea', 'Papua New Guinea'),
    ('Paraguay', 'Paraguay'),
    ('Peru', 'Peru'),
    ('Philippines', 'Philippines'),
    ('Pitcairn', 'Pitcairn'),
    ('Poland', 'Poland'),
    ('Portugal', 'Portugal'),
    ('Puerto Rico', 'Puerto Rico'),
    ('Qatar', 'Qatar'),
    ('Reunion', 'Reunion'),
    ('Romania', 'Romania'),
    ('Russian Federation', 'Russian Federation'),
    ('RWANDA', 'RWANDA'),
    ('Saint Helena', 'Saint Helena'),
    ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'),
    ('Saint Lucia', 'Saint Lucia'),
    ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'),
    ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'),
    ('Samoa', 'Samoa'),
    ('San Marino', 'San Marino'),
    ('Sao Tome and Principe', 'Sao Tome and Principe'),
    ('Saudi Arabia', 'Saudi Arabia'),
    ('Senegal', 'Senegal'),
    ('Serbia and Montenegro', 'Serbia and Montenegro'),
    ('Seychelles', 'Seychelles'),
    ('Sierra Leone', 'Sierra Leone'),
    ('Singapore', 'Singapore'),
    ('Slovakia', 'Slovakia'),
    ('Slovenia', 'Slovenia'),
    ('Solomon Islands', 'Solomon Islands'),
    ('Somalia', 'Somalia'),
    ('South Africa', 'South Africa'),
    ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'),
    ('Spain', 'Spain'),
    ('Sri Lanka', 'Sri Lanka'),
    ('Sudan', 'Sudan'),
    ('Suriname', 'Suriname'),
    ('Svalbard and Jan Mayen', 'Svalbard and Jan Mayen'),
    ('Swaziland', 'Swaziland'),
    ('Sweden', 'Sweden'),
    ('Switzerland', 'Switzerland'),
    ('Syrian Arab Republic', 'Syrian Arab Republic'),
    ('Taiwan, Province of China', 'Taiwan, Province of China'),
    ('Tajikistan', 'Tajikistan'),
    ('Tanzania, United Republic of', 'Tanzania, United Republic of'),
    ('Thailand', 'Thailand'),
    ('Timor-Leste', 'Timor-Leste'),
    ('Togo', 'Togo'),
    ('Tokelau', 'Tokelau'),
    ('Tonga', 'Tonga'),
    ('Trinidad and Tobago', 'Trinidad and Tobago'),
    ('Tunisia', 'Tunisia'),
    ('Turkey', 'Turkey'),
    ('Turkmenistan', 'Turkmenistan'),
    ('Turks and Caicos Islands', 'Turks and Caicos Islands'),
    ('Tuvalu', 'Tuvalu'),
    ('Uganda', 'Uganda'),
    ('Ukraine', 'Ukraine'),
    ('United Arab Emirates', 'United Arab Emirates'),
    ('United Kingdom', 'United Kingdom'),
    ('United States', 'United States'),
    ('United States Minor Outlying Islands', 'United States Minor Outlying Islands'),
    ('Uruguay', 'Uruguay'),
    ('Uzbekistan', 'Uzbekistan'),
    ('Vanuatu', 'Vanuatu'),
    ('Venezuela', 'Venezuela'),
    ('Viet Nam', 'Viet Nam'),
    ('Virgin Islands, British', 'Virgin Islands, British'),
    ('Virgin Islands, U.S.', 'Virgin Islands, U.S.'),
    ('Wallis and Futuna', 'Wallis and Futuna'),
    ('Western Sahara', 'Western Sahara'),
    ('Yemen', 'Yemen'),
    ('Zambia', 'Zambia'),
    ('Zimbabwe', 'Zimbabwe'),
]


class Student(models.Model):
    full_name = models.CharField(max_length=200)
    password = models.CharField(max_length=128)  # Expect hash
    authToken = models.UUIDField(default=uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return self.full_name if self.full_name else f"Student {self.id}"

class Email(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="email")
    email = models.EmailField(max_length=150, unique=True)

    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ["email"]

    def __str__(self):
        return self.full_name

class PhoneNumber(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="phone_number")
    mobile_number = models.CharField(max_length=15, unique=True)

    class Meta:
        verbose_name = "Phone Number"
        verbose_name_plural = "Phone Numbers"
        ordering = ["mobile_number"]

    def __str__(self):
        return f"{self.mobile_number}"


class StudentDetails(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='details')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    GENDERS = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDERS)
    dob = models.DateField()
    nationality = models.CharField(max_length=100)
    address = models.CharField(max_length=2000)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=12)
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)  # Updated to use COUNTRY_CHOICES with full names

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

    student = models.OneToOneField('Student', on_delete=models.CASCADE, related_name='education_details')
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

    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='experiences')
    company_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)  # Updated to use COUNTRY_CHOICES with full names
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_TYPE_CHOICES)
    industry_type = models.CharField(max_length=50, choices=INDUSTRY_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    currently_working = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.company_name} ({self.title})"


class TestScores(models.Model):
    EXAM_TYPE_CHOICES = [
        ('GRE', 'GRE'),  # Graduate Record Examinations
        ('GMAT', 'GMAT'),  # Graduate Management Admission Test
        ('TOEFL', 'TOEFL'),  # Test of English as a Foreign Language
        ('IELTS', 'IELTS'),  # International English Language Testing System
        ('SAT', 'SAT'),  # Scholastic Assessment Test
        ('ACT', 'ACT'),  # American College Testing
        ('LSAT', 'LSAT'),  # Law School Admission Test
        ('MCAT', 'MCAT'),  # Medical College Admission Test
        ('DAT', 'DAT'),  # Dental Admission Test
        ('OAT', 'OAT'),  # Optometry Admission Test
        ('PCAT', 'PCAT'),  # Pharmacy College Admission Test
        ('MAT', 'MAT'),  # Miller Analogies Test
        ('CAT', 'CAT'),  # Common Admission Test (India)
        ('GATE', 'GATE'),  # Graduate Aptitude Test in Engineering (India)
        ('GMAT-Focus', 'GMAT Focus Edition'),  # GMAT Focus Edition
    ]

    ENGLISH_EXAM_CHOICES = [
        ('TOEFL', 'TOEFL'),  # Test of English as a Foreign Language
        ('IELTS', 'IELTS'),  # International English Language Testing System
        ('PTE', 'PTE Academic'),  # Pearson Test of English Academic
        ('Duolingo', 'Duolingo English Test'),
        ('CAE', 'Cambridge English: Advanced (C1)'),  # Cambridge Advanced English
        ('CPE', 'Cambridge English: Proficiency (C2)'),  # Cambridge Proficiency English
        ('OET', 'OET'),  # Occupational English Test
        ('TOEIC', 'TOEIC'),  # Test of English for International Communication
        ('EFSET', 'EF Standard English Test'),  # EF Standard English Test
        ('CELPIP', 'CELPIP'),  # Canadian English Language Proficiency Index Program
    ]

    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name='test_scores'
    )
    exam_type = models.CharField(
        max_length=50,
        choices=EXAM_TYPE_CHOICES,
        help_text="Main aptitude exam"
    )
    english_exam_type = models.CharField(
        max_length=50,
        choices=ENGLISH_EXAM_CHOICES,
        help_text="English proficiency exam"
    )
    date = models.DateField()
    listening_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reading_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    writing_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Test Score"
        verbose_name_plural = "Test Scores"

    def __str__(self):
        return f"{self.exam_type} ({self.date})"


class Preference(models.Model):
    DEGREE_CHOICES = [
        ('High School', 'High School'),
        ('Diploma', 'Diploma'),
        ('Associate', 'Associate'),
        ('Bachelor\'s', 'Bachelor\'s'),
        ('Master\'s', 'Master\'s'),
        ('M.Phil', 'M.Phil'),
        ('Ph.D.', 'Ph.D.'),
        ('Post-Doctorate', 'Post-Doctorate'),
        ('Certificate', 'Certificate'),
        ('Other', 'Other'),
    ]

    # Static variable for discipline choices
    DISCIPLINE_CHOICES = [
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Engineering', 'Engineering'),
        ('Mathematics', 'Mathematics'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Biology', 'Biology'),
        ('Business', 'Business'),
        ('Economics', 'Economics'),
        ('Arts', 'Arts'),
        ('Law', 'Law'),
        ('Medicine', 'Medicine'),
        ('Education', 'Education'),
        ('Psychology', 'Psychology'),
        ('Social Sciences', 'Social Sciences'),
        ('Political Science', 'Political Science'),
        ('Architecture', 'Architecture'),
        ('Philosophy', 'Philosophy'),
        ('Other', 'Other'),
    ]

    # Static variable for sub-discipline choices (example sub-disciplines per discipline)
    SUB_DISCIPLINE_CHOICES = [
        ('Artificial Intelligence', 'Artificial Intelligence'),
        ('Software Engineering', 'Software Engineering'),
        ('Civil Engineering', 'Civil Engineering'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Pure Mathematics', 'Pure Mathematics'),
        ('Applied Physics', 'Applied Physics'),
        ('Organic Chemistry', 'Organic Chemistry'),
        ('Molecular Biology', 'Molecular Biology'),
        ('Finance', 'Finance'),
        ('Marketing', 'Marketing'),
        ('International Law', 'International Law'),
        ('General Medicine', 'General Medicine'),
        ('Curriculum Development', 'Curriculum Development'),
        ('Clinical Psychology', 'Clinical Psychology'),
        ('Sociology', 'Sociology'),
        ('International Relations', 'International Relations'),
        ('Urban Planning', 'Urban Planning'),
        ('Ethics', 'Ethics'),
        ('Other', 'Other'),
    ]
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='preference')
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)  # Updated to use COUNTRY_CHOICES with full names
    degree = models.CharField(max_length=100, choices=DEGREE_CHOICES)
    discipline = models.CharField(max_length=100, choices=DISCIPLINE_CHOICES)
    sub_discipline = models.CharField(max_length=100, choices=SUB_DISCIPLINE_CHOICES)
    date = models.DateField()
    budget = models.PositiveIntegerField()

    def __str__(self):
        return self.full_name


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

#     # Static variable for document status choices
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
#     status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='uploaded')
#     document_url = models.URLField(max_length=1000)

#     class Meta:
#         verbose_name = "Document"
#         verbose_name_plural = "Documents"
#         ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.doc_type}) "


class ShortlistedUniversity(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='shortlisted_universities')
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='shortlisted_by_students')
    added_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('student', 'university')
        verbose_name = "Shortlisted university"
        verbose_name_plural = "Shortlisted Universities"

    def __str__(self):
        return f"{self.student.full_name} shortlisted {self.university.name}"
    
class ShortlistedCourse(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='shortlisted_courses'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='shortlisted_by_students'
    )
    added_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = "Shortlisted Course"
        verbose_name_plural = "Shortlisted Courses"

    def __str__(self):
        return f"{self.student.full_name} shortlisted {self.course.program_name} at {self.course.university.name}"