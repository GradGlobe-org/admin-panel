import strawberry
from authentication.Schema import EmployeeQuery, EmployeeMutation, EmployeeSubscription
from blogs.Schema import BlogQuery, BlogMutation
from tasks.Schema import TaskQuery, TaskMutation


@strawberry.type
class Query:
    @strawberry.field
    def employee(self) -> EmployeeQuery:
        return EmployeeQuery()

    @strawberry.field
    def blog(self) -> BlogQuery:
        return BlogQuery()

    @strawberry.field
    def task(self) -> TaskQuery:
        return TaskQuery()


@strawberry.type
class Mutation:
    @strawberry.field
    def employee(self) -> EmployeeMutation:
        return EmployeeMutation()

    @strawberry.field
    def blog(self) -> BlogMutation:
        return BlogMutation()

    @strawberry.field
    def task(self) -> TaskMutation:
        return TaskMutation()


@strawberry.type
class Subscription(
    EmployeeSubscription,
):
    pass


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)
