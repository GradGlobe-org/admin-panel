from django.db.models.signals import post_save
from django.dispatch import receiver
from student.models import Student, TemplateDocument, StudentDocumentRequirement

def assign_template_to_student(student):
    """
    Assign all template documents to a given student if not already assigned.
    """
    template_docs = TemplateDocument.objects.all()
    existing_tdocs = set(
        StudentDocumentRequirement.objects.filter(student=student)
        .values_list('template_document_id', flat=True)
    )
    new_reqs = [
        StudentDocumentRequirement(student=student, template_document=tdoc)
        for tdoc in template_docs if tdoc.id not in existing_tdocs
    ]
    if new_reqs:
        StudentDocumentRequirement.objects.bulk_create(new_reqs)

def assign_student_to_template(tdoc):
    """
    Assign a new template document to all existing students.
    """
    students = Student.objects.all()
    existing_reqs = set(
        StudentDocumentRequirement.objects.filter(template_document=tdoc)
        .values_list('student_id', flat=True)
    )
    new_reqs = [
        StudentDocumentRequirement(student=student, template_document=tdoc)
        for student in students if student.id not in existing_reqs
    ]
    if new_reqs:
        StudentDocumentRequirement.objects.bulk_create(new_reqs)

# Signals remain the same
@receiver(post_save, sender=Student)
def student_created_assign_templates(sender, instance, created, **kwargs):
    if created:
        assign_template_to_student(instance)

@receiver(post_save, sender=TemplateDocument)
def template_created_assign_to_students(sender, instance, created, **kwargs):
    if created:
        assign_student_to_template(instance)
