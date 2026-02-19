from django.apps import apps
from django.http import HttpResponse
from django.db.models import OneToOneRel, ForeignKey
from openpyxl import Workbook


def get_model_fields(model_name, app_label, excluded_fields_dict=None, related_models_map=None):
    model = apps.get_model(app_label, model_name)

    excluded_fields_dict = excluded_fields_dict or {}
    related_models_map = related_models_map or {}

    excluded_fields = excluded_fields_dict.get(model_name, [])
    allowed_related = related_models_map.get(model_name, [])

    fields = []

    # ✅ Direct fields
    for field in model._meta.get_fields():

        if isinstance(field, OneToOneRel):
            continue

        if (
            field.auto_created
            or not field.concrete
            or field.primary_key
            or not field.editable
        ):
            continue

        if field.name in excluded_fields:
            continue

        if isinstance(field, ForeignKey):
            fields.append(f"{field.name}_id")
        else:
            fields.append(field.name)

    # ✅ Controlled OneToOne flattening
    for field in model._meta.get_fields():

        if isinstance(field, OneToOneRel):

            related_model = field.related_model
            related_model_name = related_model.__name__

            if related_model_name not in allowed_related:
                continue

            related_excluded = excluded_fields_dict.get(related_model_name, [])

            for rel_field in related_model._meta.get_fields():

                if (
                    rel_field.auto_created
                    or not rel_field.concrete
                    or rel_field.primary_key
                    or not rel_field.editable
                ):
                    continue

                if rel_field.name in related_excluded:
                    continue

                if isinstance(rel_field, ForeignKey):
                    continue

                fields.append(rel_field.name)

    return fields

def generate_excel_file(
    model_names,
    app_label,
    excluded_fields_dict=None,
    related_models_map=None
):
    wb = Workbook()

    for index, model_name in enumerate(model_names):

        if index == 0:
            ws = wb.active
            ws.title = model_name
        else:
            ws = wb.create_sheet(title=model_name)

        fields = get_model_fields(
            model_name,
            app_label,
            excluded_fields_dict,
            related_models_map
        )

        ws.append(fields)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="sample_template.xlsx"'

    wb.save(response)
    return response


def download_sample(request):
    MODELS = ["Student"]

    EXCLUDED_FIELDS = {
        "Student": ["is_otp_verified", "authToken"],
        "Email": [],
        "StudentDetails": [],
    }

    RELATED_MODELS_TO_INCLUDE = {
        "Student": ["Email", "StudentDetails"]
    }

    return generate_excel_file(
        MODELS,
        app_label="student",
        excluded_fields_dict=EXCLUDED_FIELDS,
        related_models_map=RELATED_MODELS_TO_INCLUDE
    )
