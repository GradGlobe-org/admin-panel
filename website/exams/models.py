from django.db import models
from authentication.models import Employee
from student.models import Student
from django.utils import timezone

# ----------------------------
# Test model
# ----------------------------
class Test(models.Model):
    PRIORITY = [
        ("low", "LOW"),
        ("med", "MEDIUM"),
        ("high", "HIGH")
    ]

    title = models.CharField(max_length=1000)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    priority = models.CharField(max_length=10, choices=PRIORITY, default="low")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tests"
    )
    total_marks = models.FloatField(default=0)  # Auto-calculated
    # Negative marking for MCQs. Choices: 0 (none), 0.25, 0.5, 0.33, 0.2
    NEGATIVE_CHOICES = [
        (0, "None"),
        (0.25, "1/4"),
        (0.5, "1/2"),
        (0.33, "1/3"),
        (0.2, "1/5"),
    ]
    negative_marking_factor = models.FloatField(choices=NEGATIVE_CHOICES, default=0)

    def __str__(self):
        return self.title

    def calculate_total_marks(self):
        """Automatically sum all question marks."""
        total = self.questions.aggregate(models.Sum('marks'))['marks__sum'] or 0
        self.total_marks = total
        self.save()
        return self.total_marks


# ----------------------------
# Course model
# ----------------------------
class CourseCategories(models.Model):
    name = models.CharField(max_length=1000, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    category = models.ForeignKey(CourseCategories, on_delete=models.SET_NULL, null=True, blank=True)
    mentor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    featured_image = models.TextField(default="", null=True, blank=True)
    image_uuid = models.UUIDField(editable=False, unique=True, null=True, blank=True)
    google_file_id = models.CharField(max_length=255, blank=True, default="", null=True)
    tests = models.ManyToManyField(Test, through='CourseTest', related_name="courses", blank=True)
    course_duration = models.PositiveIntegerField(default=1, help_text="Time taken to complete course")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CourseLinkedStudent(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrolled_students")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrolled_courses")
    expiration = models.DateTimeField()
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("course", "student")

    def __str__(self):
        return f"{self.student} -> {self.course}"


# ----------------------------
# Through table for Course -> Test ordering
# ----------------------------
class CourseTest(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'test')

    def __str__(self):
        return f"{self.course.name} - {self.test.title} (Order {self.order})"


# ----------------------------
# Question model
# ----------------------------
class Question(models.Model):
    QUESTION_TYPES = [
        ("MCQ", "Multiple Choice"),
        ("SUB", "Subjective"),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPES)
    marks = models.FloatField(default=1.0)
    is_single_answer = models.BooleanField(default=True)
    order = models.PositiveBigIntegerField(default=0, null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.test.title} - {self.question[:50]}"


# ----------------------------
# Option model
# ----------------------------
class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    option_name = models.CharField(max_length=5000)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_name


# ----------------------------
# Test assignment to students
# ----------------------------
class TestStatus(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
        ("expired", "Expired"),
    ]

    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, related_name="test_statuses")
    test = models.ForeignKey(Test, on_delete=models.SET_NULL, null=True, related_name="statuses")
    assigned_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "test")

    def is_active(self):
        """Check if the student can still attempt the test."""
        now = timezone.now()
        return self.status in ["pending", "ongoing"] and now <= self.deadline

    def __str__(self):
        return f"{self.student} - {self.test} ({self.status})"


# ----------------------------
# Store student answers for later evaluation
# ----------------------------
class Answer(models.Model):
    test_status = models.ForeignKey(TestStatus, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(Option, blank=True)  # For MCQs
    subjective_answer = models.TextField(blank=True, null=True)    # For subjective
    marks_obtained = models.FloatField(default=0)  # per-question evaluation
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test_status.student} - {self.question[:50]}"


# ----------------------------
# Evaluation table for storing marks
# ----------------------------
class Evaluation(models.Model):
    test_status = models.OneToOneField(TestStatus, on_delete=models.CASCADE, related_name="evaluation")
    total_marks = models.FloatField(default=0)
    obtained_marks = models.FloatField(default=0)
    evaluated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True, null=True)
    evaluated_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="evaluations")

    def __str__(self):
        return f"{self.test_status.student} - {self.test_status.test.title} Evaluation"