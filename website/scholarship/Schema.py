import strawberry
from typing import List, Optional, Annotated
from django.db.models import Q
from graphql import GraphQLError
from authentication.Utils import SchemaMixin
from scholarship.models import Scholarship
from university.models import Country


@strawberry.type(description="Represents an expense type for scholarships")
class ExpenseTypeSchema:
    name: str = strawberry.field(description="Name of the expense type")

@strawberry.type(description="Represents a university")
class UniSchema:
    id: int = strawberry.field(description="University ID")
    name: str = strawberry.field(description="University name")

@strawberry.type(description="Represents a country")
class CountryNameSchema(SchemaMixin):
    id: int = strawberry.field(description="Country ID")
    name: str = strawberry.field(description="Country name")

    @classmethod
    def country_list(cls, auth_token: str) -> List["CountryNameSchema"]:
        try:
            emp = cls.get_employee(auth_token)
            if not emp:
                raise GraphQLError("Unauthorized")

            if not emp.is_superuser:
                has_permission = emp.job_roles.filter(
                    permissions__name="country_view"
                ).exists()

                if not has_permission:
                    raise GraphQLError("Unauthorized")

            countries = Country.objects.all().order_by("name")

            return [
                cls(
                    id=country.id,
                    name=country.name
                )
                for country in countries
            ]

        except:
            raise GraphQLError("Internal Server Error")

@strawberry.type(description="Represents scholarship expense coverage")
class ScholarshipExpenseCoverageSchema:
    expense_type: ExpenseTypeSchema = strawberry.field(description="Covered expense type")
    is_covered: bool = strawberry.field(description="Whether the expense is covered")

@strawberry.type(description="Represents scholarship FAQs")
class FAQSchema:
    question: str = strawberry.field(description="FAQ question")
    answer: str = strawberry.field(description="FAQ answer")

@strawberry.type(description="Represents a scholarship")
class ScholarshipSchema(SchemaMixin):
    id: int
    name: str = strawberry.field(description="Scholarship name")
    awarded_by: str = strawberry.field(description="Scholarship provider")
    overview: str = strawberry.field(description="Short scholarship summary")
    details: str = strawberry.field(description="Detailed scholarship info")
    amount_details: str = strawberry.field(description="Scholarship amount breakdown")
    course: str = strawberry.field(description="Eligible course")
    deadline: str = strawberry.field(description="Application deadline")
    intake_year: str = strawberry.field(description="Applicable intake year")
    amount: str = strawberry.field(description="Total scholarship amount")
    country: str = strawberry.field(description="Scholarship country")
    no_of_students: str = strawberry.field(description="Number of recipients")
    type_of_scholarship: str = strawberry.field(description="Scholarship category")
    brochure: Optional[str] = strawberry.field(default=None, description="Brochure URL")

    university: List[UniSchema] = strawberry.field(description="Associated universities")
    eligible_nationalities: List[CountryNameSchema] = strawberry.field(description="Eligible countries")

    scholarship_expense: List[ScholarshipExpenseCoverageSchema] = strawberry.field(description="Expense coverage details")
    faqs: List[FAQSchema] = strawberry.field(description="Frequently asked questions")

@strawberry.type
class ScholarshipListSchema(SchemaMixin):
    scholarship : List[ScholarshipSchema]
    page: int
    limit: int
    total: int

    @classmethod
    def scholarships(cls,
                     auth_token: Annotated[str, strawberry.field(description="Authorization token")],
                     page: int,
                     limit: int,
                     query: Annotated[Optional[str], strawberry.field(description="Search keyword for name, course, or awarded_by")] = None,
                     country_id: Annotated[Optional[int], strawberry.field(description="Filter scholarships by country ID")] = None,
                     scholarship_id: Annotated[Optional[int], strawberry.field(description="Fetch a specific scholarship by ID")]= None
                     ) -> "ScholarshipListSchema":

        try:
            emp = cls.get_employee(auth_token)
        except:
            raise GraphQLError("Unauthorized")
        if not emp:
            raise GraphQLError("Unauthorized")

        if not emp.is_superuser:
            has_permission = emp.job_roles.filter(
                permissions__name="scholarship_view"
            ).exists()
            if not has_permission:
                raise GraphQLError("Insufficient Permissions")

        if scholarship_id and (query or country_id):
            raise GraphQLError("Please provide either scholarship_id or query and/or country")

        page = max(1, page)
        limit = min(max(1, limit), 100)
        offset = (page - 1) * limit

        qs = Scholarship.objects.select_related("country").prefetch_related(
            "university",
            "eligible_nationalities",
            "expense_coverages__expense_type",
            "faqs"
        )
        if scholarship_id:
            qs = qs.filter(id=scholarship_id)
        if country_id:
            qs = qs.filter(country_id=country_id)
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(course__icontains=query) |
                Q(awarded_by__icontains=query)
            )

        total = qs.count()
        qs = qs[offset: offset + limit]
        results = []

        for sch in qs:
            universities = [
                UniSchema(
                    id=uni.id,
                    name=uni.name
                )
                for uni in sch.university.all()
            ]

            countries = [
                CountryNameSchema(
                    id=country.id,
                    name=country.name
                )
                for country in sch.eligible_nationalities.all()
            ]

            expenses = [
                ScholarshipExpenseCoverageSchema(
                    expense_type=ExpenseTypeSchema(
                        name=exp.expense_type.name
                    ),
                    is_covered=exp.is_covered
                )
                for exp in sch.expense_coverages.all()
            ]

            faqs = [
                FAQSchema(
                    question=faq.question,
                    answer=faq.answer
                )
                for faq in sch.faqs.all()
            ]

            scholarship_obj = ScholarshipSchema(
                id=sch.id,
                name=sch.name,
                awarded_by=sch.awarded_by,
                overview=sch.overview,
                details=sch.details,
                amount_details=sch.amount_details,
                course=sch.course,
                deadline=str(sch.deadline),
                intake_year=str(sch.intake_year),
                amount=str(sch.amount),
                country=sch.country.name,
                no_of_students=sch.no_of_students,
                type_of_scholarship=sch.type_of_scholarship,
                brochure=sch.brochure,

                university=universities,
                eligible_nationalities=countries,
                scholarship_expense=expenses,
                faqs=faqs,
            )
            results.append(scholarship_obj)

        return cls(
            scholarship=results,
            page=page,
            limit=limit,
            total=total
        )

@strawberry.type
class ScholarshipQuery:
    scholarship_list : ScholarshipListSchema = strawberry.field(
        resolver=ScholarshipListSchema.scholarships,
    )

    country_list : List[CountryNameSchema] = strawberry.field(
        resolver=CountryNameSchema.country_list,
    )




