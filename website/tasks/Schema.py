import uuid

import strawberry
from typing import Optional, Annotated, List, Any, Awaitable
from datetime import datetime

from django.contrib.gis.gdal.prototypes.geom import assign_srs
from strawberry.scalars import JSON

# get_my_created_tasks/owned_task
# get_all_my_tasks
# edit_task
# edit_task_assignment/unassign/assign
# delete_task


@strawberry.type
class TaskSchema:
    id: int
    title: str
    description: str
    priority: int
    status: str
    created_at: datetime
    due_date: datetime
    assigned_students: JSON
    assigned_employees: JSON

    @classmethod
    def get_owned_tasks(cls, auth_token:uuid.UUID):
