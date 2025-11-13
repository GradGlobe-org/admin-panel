from django.db.models.signals import post_save
from django.dispatch import receiver
from student.models import Student, TemplateDocument, StudentDocumentRequirement

def assign_template_to_student(student):
    """
    Assign all template documents to a given student if not already assigned.
    """
    template_docs = TemplateDocument.objects.all()
    for tdoc in template_docs:
        StudentDocumentRequirement.objects.get_or_create(
            student=student,
            template_document=tdoc
        )

def assign_student_to_template(tdoc):
    """
    Assign a new template document to all existing students.
    """
    students = Student.objects.all()
    for student in students:
        StudentDocumentRequirement.objects.get_or_create(
            student=student,
            template_document=tdoc
        )

# When a new student is created
@receiver(post_save, sender=Student)
def student_created_assign_templates(sender, instance, created, **kwargs):
    if created:
        assign_template_to_student(instance)

# When a new TemplateDocument is created
@receiver(post_save, sender=TemplateDocument)
def template_created_assign_to_students(sender, instance, created, **kwargs):
    if created:
        assign_student_to_template(instance)