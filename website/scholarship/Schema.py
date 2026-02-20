import datetime

import strawberry
from typing import List, Optional, Annotated

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from graphql import GraphQLError
from authentication.Utils import SchemaMixin
from scholarship.models import Scholarship, ExpenseType, ScholarshipExpenseCoverage, FAQ
from university.models import Country, university


@strawberry.type(description="Represents an expense type for scholarships")
class ExpenseTypeSchema(SchemaMixin):
    id: int
    name: str = strawberry.field(description="Name of the expense type")

    @classmethod
    def expense_type_list(cls, auth_token: str) -> List["ExpenseTypeSchema"]:
        try:
            emp = cls.get_employee(auth_token)
        except:
            raise GraphQLError("Unauthorized")
        if not emp:
            raise GraphQLError("Unauthorized")
        if not emp.is_superuser:
            has_permission = emp.job_roles.filter(
                Q(permissions__name="scholarship_add") |
                Q(permissions__name="scholarship_update")
            ).exists()
            if not has_permission:
                raise GraphQLError("Insufficient Permissions")

        try:
            expense_types = ExpenseType.objects.all().order_by("name")
            return [
                cls(
                    id=expense_type.id,
                    name=expense_type.name,
                )
                for expense_type in expense_types
            ]
        except:
            raise GraphQLError("Error getting expense types")


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
    id: int
    expense_type: ExpenseTypeSchema = strawberry.field(description="Covered expense type")
    is_covered: bool = strawberry.field(description="Whether the expense is covered")

@strawberry.type(description="Represents scholarship FAQs")
class FAQSchema:
    id: int
    question: str = strawberry.field(description="FAQ question")
    answer: str = strawberry.field(description="FAQ answer")

@strawberry.input
class ExpenseCoverageInputSchema:
    expense_type_id: int = strawberry.field(description="Expense type ID")
    is_covered: bool = strawberry.field(description="Whether the expense is covered")

@strawberry.input
class FAQInputSchema:
    question: str = strawberry.field(description="FAQ question")
    answer: str  =strawberry.field(description="FAQ answer")

@strawberry.input
class ScholarshipInputSchema:
    name: str = strawberry.field(description="Scholarship name")
    awarded_by: str = strawberry.field(description="Scholarship provider")
    overview: str = strawberry.field(description="Short scholarship summary")
    details: str = strawberry.field(description="Detailed scholarship info")
    amount_details: str = strawberry.field(description="Scholarship amount breakdown")
    course: str = strawberry.field(description="Eligible course")
    deadline: datetime.date = strawberry.field(description="Application deadline")
    intake_year: datetime.date = strawberry.field(description="Applicable intake year")
    amount: int = strawberry.field(description="Total scholarship amount")
    no_of_students: str = strawberry.field(description="Number of recipients")
    type_of_scholarship: str = strawberry.field(description="Scholarship category")
    brochure: Optional[str] = strawberry.field(default=None, description="Brochure URL")

    country_id: int = strawberry.field(description="Scholarship country")
    university_ids: List[int] = strawberry.field(description="Ids of the universities scholarship applies on")
    eligible_nationalities_ids: List[int] = strawberry.field(description="Ids of countries whose citizens are eligible for this scholarship")

@strawberry.input
class ScholarshipExpenseCoverageSchemaUpdateInput:
    id: int
    expense_type_id: Optional[int] = strawberry.field(default=None, description="Covered expense type")
    is_covered: Optional[bool] = strawberry.field(default=None, description="Whether the expense is covered")

@strawberry.input
class UpdateExpenseSchema:
    add: Optional[List[ExpenseCoverageInputSchema]] = None
    update: Optional[List[ScholarshipExpenseCoverageSchemaUpdateInput]] = None
    delete: Optional[List[int]] = None

@strawberry.input
class FAQUpdateSchema:
    id: int
    question: Optional[str] = strawberry.field(default= None, description="FAQ question")
    answer: Optional[str] = strawberry.field(default = None, description="FAQ answer")

@strawberry.input
class FAQUpdateInputSchema:
    add: list[FAQInputSchema] = None
    update: list[FAQUpdateSchema] = None
    delete: list[int] = None


@strawberry.input
class ScholarshipUpdateInputSchema:
    name: Optional[str] = strawberry.field(default=None, description="Scholarship name")
    awarded_by: Optional[str] = strawberry.field(default=None, description="Scholarship provider")
    overview: Optional[str] = strawberry.field(default=None, description="Short scholarship summary")
    details: Optional[str] = strawberry.field(default=None, description="Detailed scholarship info")
    amount_details: Optional[str] = strawberry.field(default=None, description="Scholarship amount breakdown")
    course: Optional[str] = strawberry.field(default=None, description="Eligible course")
    deadline: Optional[datetime.date] = strawberry.field(default=None, description="Application deadline")
    intake_year: Optional[datetime.date] = strawberry.field(default=None, description="Applicable intake year")
    amount: Optional[int] = strawberry.field(default=None, description="Total scholarship amount")
    no_of_students: Optional[str] = strawberry.field(default=None, description="Number of recipients")
    type_of_scholarship: Optional[str] = strawberry.field(default=None, description="Scholarship category")
    brochure: Optional[str] = strawberry.field(default=None, description="Brochure URL")
    country_id: Optional[int] = strawberry.field(default=None, description="Scholarship country")

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

    @classmethod
    def add_scholarship(cls,
                        auth_token : Annotated[str, strawberry.field(description="Authorization token")],
                        scholarship : ScholarshipInputSchema,
                        expenses : List[ExpenseCoverageInputSchema],
                        faqs : List[FAQInputSchema],
                        ) -> "ScholarshipSchema":

        try:
            emp = cls.get_employee(auth_token)
        except:
            raise GraphQLError("Unauthorized")
        if not emp:
            raise GraphQLError("Unauthorized")
        if not emp.is_superuser:
            has_permission = emp.job_roles.filter(
                permissions__name="scholarship_add"
            ).exists()
            if not has_permission:
                raise GraphQLError("Insufficient Permissions")

        try:
            with transaction.atomic():
                if scholarship:
                    country = Country.objects.get(id=scholarship.country_id)
                    unis = university.objects.filter(
                        id__in=scholarship.university_ids
                    )
                    elig_nat = Country.objects.filter(
                        id__in=scholarship.eligible_nationalities_ids
                    )

                    sch = Scholarship.objects.create(
                        name=scholarship.name,
                        awarded_by=scholarship.awarded_by,
                        overview=scholarship.overview,
                        details=scholarship.details,
                        amount_details=scholarship.amount_details,
                        course=scholarship.course,
                        deadline=scholarship.deadline,
                        intake_year=scholarship.intake_year,
                        amount=scholarship.amount,
                        country=country,
                        no_of_students=scholarship.no_of_students,
                        type_of_scholarship=scholarship.type_of_scholarship,
                        brochure=scholarship.brochure or None,
                    )
                    sch.university.set(unis)
                    sch.eligible_nationalities.set(elig_nat)

                    if expenses:
                        for exp in expenses:
                            try:
                                expense_type = ExpenseType.objects.get(id=exp.expense_type_id)
                            except ExpenseType.DoesNotExist:
                                raise GraphQLError("Invalid expense type")

                            ScholarshipExpenseCoverage.objects.create(
                                scholarship=sch,
                                expense_type=expense_type,
                                is_covered=exp.is_covered,
                            )
                    if faqs:
                        for faq in faqs:
                            FAQ.objects.create(
                                question=faq.question,
                                answer=faq.answer,
                                scholarship=sch,
                            )
                    sch.save()

        except:
            raise GraphQLError("Internal Server Error")

        return ScholarshipSchema(
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
            university=[
                UniSchema(id=u.id, name=u.name)
                for u in sch.university.all()
            ],
            eligible_nationalities=[
                CountryNameSchema(id=c.id, name=c.name)
                for c in sch.eligible_nationalities.all()
            ],
            scholarship_expense=[
                ScholarshipExpenseCoverageSchema(
                    id=e.id,
                    expense_type=ExpenseTypeSchema(id=e.expense_type.id, name=e.expense_type.name),
                    is_covered=e.is_covered
                )
                for e in sch.expense_coverages.all()
            ],
            faqs=[
                FAQSchema(id=f.id, question=f.question, answer=f.answer)
                for f in sch.faqs.all()
            ],
        )

    @classmethod
    def update_scholarship(cls,
                           auth_token : Annotated[str, strawberry.field(description="Authorization token")],
                           scholarship_id: int,
                           updated_scholarship: Optional[ScholarshipUpdateInputSchema] = None,
                           remove_university_ids: Optional[List[int]] = None,
                           add_university_ids: Optional[List[int]] = None,
                           remove_eligible_country_ids: Optional[List[int]] = None,
                           add_eligible_country_ids: Optional[List[int]] = None,
                           expense: Optional[UpdateExpenseSchema] = None,
                           faqs: Optional[FAQUpdateInputSchema] = None,
                           ) -> "ScholarshipSchema":

        try:
            emp = cls.get_employee(auth_token)
        except:
            raise GraphQLError("Unauthorized")
        if not emp:
            raise GraphQLError("Unauthorized")
        if not emp.is_superuser:
            has_permission = emp.job_roles.filter(
                permissions__name="scholarship_update"
            ).exists()
            if not has_permission:
                raise GraphQLError("Insufficient Permissions")

        try:
            sch = Scholarship.objects.get(id=scholarship_id)
        except ObjectDoesNotExist:
            raise GraphQLError("Scholarship not found")
        except:
            raise GraphQLError("Object does not exist")

        with transaction.atomic():
            if updated_scholarship:
                if updated_scholarship.name is not None:
                    sch.name = updated_scholarship.name
                if updated_scholarship.awarded_by is not None:
                    sch.awarded_by = updated_scholarship.awarded_by
                if updated_scholarship.overview is not None:
                    sch.overview = updated_scholarship.overview
                if updated_scholarship.details is not None:
                    sch.details = updated_scholarship.details
                if updated_scholarship.amount_details is not None:
                    sch.amount_details = updated_scholarship.amount_details
                if updated_scholarship.course is not None:
                    sch.course = updated_scholarship.course
                if updated_scholarship.deadline is not None:
                    sch.deadline = updated_scholarship.deadline
                if updated_scholarship.intake_year is not None:
                    sch.intake_year = updated_scholarship.intake_year
                if updated_scholarship.amount is not None:
                    sch.amount = updated_scholarship.amount
                if updated_scholarship.no_of_students is not None:
                    sch.no_of_students = updated_scholarship.no_of_students
                if updated_scholarship.type_of_scholarship is not None:
                    sch.type_of_scholarship = updated_scholarship.type_of_scholarship
                if updated_scholarship.brochure is not None:
                    sch.brochure = updated_scholarship.brochure
                if updated_scholarship.country_id is not None:
                    if not Country.objects.filter(
                            id=updated_scholarship.country_id
                    ).exists():
                        raise GraphQLError("Invalid Country")
                    sch.country_id = updated_scholarship.country_id

            if remove_university_ids:
                universities = university.objects.filter(id__in=remove_university_ids)
                sch.university.remove(*universities)

            if add_university_ids:
                universities = university.objects.filter(id__in=add_university_ids)
                sch.university.add(*universities)

            if remove_eligible_country_ids:
                countries = Country.objects.filter(id__in=remove_eligible_country_ids)
                sch.eligible_nationalities.remove(*countries)

            if add_eligible_country_ids:
                countries = Country.objects.filter(id__in=add_eligible_country_ids)
                sch.eligible_nationalities.add(*countries)

            if expense:
                if expense.delete:
                    ScholarshipExpenseCoverage.objects.filter(
                        id__in=expense.delete,
                        scholarship=sch
                    ).delete()

                if expense.add:
                    new_objects = []

                    for ex in expense.add:
                        new_objects.append(
                            ScholarshipExpenseCoverage(
                                scholarship=sch,
                                expense_type_id=ex.expense_type_id,
                                is_covered=ex.is_covered
                            )
                        )

                    ScholarshipExpenseCoverage.objects.bulk_create(new_objects)

                if expense.update:
                    for ex in expense.update:
                        qs = ScholarshipExpenseCoverage.objects.filter(
                            id=ex.id,
                            scholarship=sch
                        )
                        if not qs.exists():
                            raise GraphQLError(f"Invalid expense ID: {ex.id}")
                        update_data = {}
                        if ex.expense_type_id is not None:
                            update_data["expense_type_id"] = ex.expense_type_id
                        if ex.is_covered is not None:
                            update_data["is_covered"] = ex.is_covered
                        if update_data:
                            qs.update(**update_data)

            if faqs:
                if faqs.delete:
                    FAQ.objects.filter(
                        id__in=faqs.delete,
                        scholarship=sch
                    ).delete()

                if faqs.add:
                    new_objects = []
                    for faq in faqs.add:
                        new_objects.append(
                            FAQ(
                                question=faq.question,
                                answer=faq.answer,
                                scholarship=sch
                            )
                        )
                    FAQ.objects.bulk_create(new_objects)

                if faqs.update:
                    for faq in faqs.update:
                        qs = FAQ.objects.filter(
                            id=faq.id,
                            scholarship=sch
                        )
                        if not qs.exists():
                            raise GraphQLError(f"Invalid FAQ ID{faq.id}")
                        update_data = {}
                        if faq.question is not None:
                            update_data["question"] = faq.question
                        if faq.answer is not None:
                            update_data["answer"] = faq.answer
                        if update_data:
                            qs.update(**update_data)

            sch.save()


        return ScholarshipSchema(
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
            university=[
                UniSchema(id=u.id, name=u.name)
                for u in sch.university.all()
            ],
            eligible_nationalities=[
                CountryNameSchema(id=c.id, name=c.name)
                for c in sch.eligible_nationalities.all()
            ],
            scholarship_expense=[
                ScholarshipExpenseCoverageSchema(
                    id=e.id,
                    expense_type=ExpenseTypeSchema(id=e.expense_type.id, name=e.expense_type.name),
                    is_covered=e.is_covered
                )
                for e in sch.expense_coverages.all()
            ],
            faqs=[
                FAQSchema(id=f.id, question=f.question, answer=f.answer)
                for f in sch.faqs.all()
            ],
        )




@strawberry.input
class ScholarshipUpdateInputSchema:
    name: Optional[str] = strawberry.field(default=None, description="Scholarship name")
    awarded_by: Optional[str] = strawberry.field(default=None, description="Scholarship provider")
    overview: Optional[str] = strawberry.field(default=None, description="Short scholarship summary")
    details: Optional[str] = strawberry.field(default=None, description="Detailed scholarship info")
    amount_details: Optional[str] = strawberry.field(default=None,
                                                     description="Scholarship amount breakdown")
    course: Optional[str] = strawberry.field(default=None, description="Eligible course")
    deadline: Optional[datetime.date] = strawberry.field(default=None,
                                                         description="Application deadline")
    intake_year: Optional[datetime.date] = strawberry.field(default=None,
                                                            description="Applicable intake year")
    amount: Optional[int] = strawberry.field(default=None, description="Total scholarship amount")
    no_of_students: Optional[str] = strawberry.field(default=None, description="Number of recipients")
    type_of_scholarship: Optional[str] = strawberry.field(default=None,
                                                          description="Scholarship category")
    brochure: Optional[str] = strawberry.field(default=None, description="Brochure URL")
    country_id: Optional[int] = strawberry.field(default=None, description="Scholarship country")


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
                    id=exp.id,
                    expense_type=ExpenseTypeSchema(
                        id=exp.id,
                        name=exp.expense_type.name
                    ),
                    is_covered=exp.is_covered
                )
                for exp in sch.expense_coverages.all()
            ]
            faqs = [
                FAQSchema(
                    id=faq.id,
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

    expense_type_list : List[ExpenseTypeSchema] = strawberry.field(
        resolver=ExpenseTypeSchema.expense_type_list,
    )

@strawberry.type
class ScholarshipMutation:
    add_scholarship : ScholarshipSchema = strawberry.field(
        resolver=ScholarshipSchema.add_scholarship
    )


