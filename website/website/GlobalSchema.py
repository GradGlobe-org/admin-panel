import strawberry
from authentication.Schema import EmployeeQuery, EmployeeMutation, EmployeeSubscription


@strawberry.type
class Query:
    @strawberry.field
    def employee(self) -> EmployeeQuery:
        return EmployeeQuery()


@strawberry.type
class Mutation:
    @strawberry.field
    def employee(self) -> EmployeeMutation:
        return EmployeeMutation()


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
