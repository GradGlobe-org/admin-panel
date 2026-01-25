import strawberry
from strawberry.extensions import QueryDepthLimiter, MaxAliasesLimiter, MaxTokensLimiter
from strawberry.schema.config import StrawberryConfig
from authentication.Schema import EmployeeQuery, EmployeeMutation, EmployeeSubscription
from blogs.Schema import BlogQuery, BlogMutation
from tasks.Schema import TaskQuery, TaskMutation
from university.Schema import UniversityQuery

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

    @strawberry.field
    def university(self) -> UniversityQuery:
        return UniversityQuery()


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


config = StrawberryConfig(batching_config={"max_operations": 10})

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[QueryDepthLimiter(max_depth=6), MaxAliasesLimiter(max_alias_count=10),
                MaxTokensLimiter(max_token_count=1000)],
    config=config,
)
