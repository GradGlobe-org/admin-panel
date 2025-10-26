# admin.py
from django.contrib import admin
import nested_admin

from .models import (
    TestRules, Test, TestSection, Question, Option,
    CourseCategories, Course, CourseLinkedStudent, CourseTest,
    TestStatus, Answer, Evaluation
)

# ----------------------------
# Inline for Options (nested inside Question)
# ----------------------------
class OptionInline(nested_admin.NestedTabularInline):
    model = Option
    extra = 2


# ----------------------------
# Inline for Questions (nested inside Section)
# ----------------------------
class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    inlines = [OptionInline]
    extra = 1


# ----------------------------
# Inline for Test Sections (nested inside Test)
# ----------------------------
class TestSectionInline(nested_admin.NestedStackedInline):
    model = TestSection
    inlines = [QuestionInline]
    extra = 1


# ----------------------------
# Test Admin
# ----------------------------
@admin.register(Test)
class TestAdmin(nested_admin.NestedModelAdmin):
    list_display = ("title", "priority", "total_marks", "created_by_employee", "created_at")
    list_filter = ("priority", "created_at")
    search_fields = ("title", "description")
    inlines = [TestSectionInline]


# ----------------------------
# Test Rules Admin
# ----------------------------
@admin.register(TestRules)
class TestRulesAdmin(admin.ModelAdmin):
    list_display = ("name", "added_by", "created_at")
    search_fields = ("name", "text")


# ----------------------------
# Course Admin
# ----------------------------
@admin.register(CourseCategories)
class CourseCategoriesAdmin(admin.ModelAdmin):
    list_display = ("name",)


class CourseTestInline(admin.TabularInline):
    model = CourseTest
    extra = 1


class CourseLinkedStudentInline(admin.TabularInline):
    model = CourseLinkedStudent
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "mentor", "course_duration", "created_at")
    search_fields = ("name", "description")
    inlines = [CourseTestInline, CourseLinkedStudentInline]


# ----------------------------
# Test Status Admin (Answers inline here)
# ----------------------------
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


@admin.register(TestStatus)
class TestStatusAdmin(admin.ModelAdmin):
    list_display = ("student", "test", "status", "assigned_at", "deadline", "started_at", "completed_at")
    list_filter = ("status", "assigned_at")
    search_fields = ("student__name", "test__title")
    inlines = [AnswerInline]


# ----------------------------
# Evaluation Admin
# ----------------------------
@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("test_status", "total_marks", "obtained_marks", "evaluated_by", "evaluated_at")
    search_fields = ("test_status__student__name", "test_status__test__title")


# ----------------------------
# Register leftover models directly
# ----------------------------
admin.site.register(CourseTest)
admin.site.register(CourseLinkedStudent)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Answer)