import strawberry
from authentication.Schema import EmployeeQuery, EmployeeMutation, EmployeeSubscription
from blogs.Schema import BlogQuery, BlogMutation


@strawberry.type
class Query:
    @strawberry.field
    def employee(self) -> EmployeeQuery:
        return EmployeeQuery()

    @strawberry.field
    def blog(self) -> BlogQuery:
        return BlogQuery()


@strawberry.type
class Mutation:
    @strawberry.field
    def employee(self) -> EmployeeMutation:
        return EmployeeMutation()

    @strawberry.field
    def blog(self) -> BlogMutation:
        return BlogMutation()


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
