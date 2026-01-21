import uuid
from authentication.models import Employee


class SchemaMixin:
    @classmethod
    def get_employee(cls, authkey: str):
        try:
            try:
                uuid.UUID(authkey)
            except ValueError:
                return False
            emp = Employee.objects.get(authToken=authkey)
        except Exception as e:
            print(e)
            return False
        return emp
