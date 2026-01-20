import uuid
from authentication.models import Employee


class SchemaMixin:
    @classmethod
    def is_superuser(cls, authkey: str):
        try:
            try:
                uuid.UUID(authkey)
            except ValueError:
                return False
            emp = Employee.objects.get(authToken=authkey)
        except Exception as e:
            return False
        if emp.is_superuser:
            return True
        return False

