import decimal
import uuid

import strawberry
from typing import Optional, Annotated, List, Any, Awaitable
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from sqlalchemy import false

from authentication.models import Employee
from strawberry.exceptions import GraphQLError
from university.models import *


# country related

@strawberry.type
class CountryFaqSchema:
    id: int
    question: str
    answer: str


@strawberry.type
class WhyStudyInSectionSchema:
    content: str


@strawberry.type
class CountryFactSchema:
    id: int
    name: str


@strawberry.type
class CostOfLivingSchema:
    rent_min: decimal.Decimal
    rent_max: decimal.Decimal
    food_min: decimal.Decimal
    food_max: decimal.Decimal
    transport_min: decimal.Decimal
    transport_max: decimal.Decimal
    miscellaneous_min: decimal.Decimal
    miscellaneous_max: decimal.Decimal
    total_min: decimal.Decimal
    total_max: decimal.Decimal


@strawberry.type
class VisaSchema:
    id: int
    name: str
    type_of_visa: str
    cost: int
    describe: str

# university related

@strawberry.type
class LocationSchema:
    id: int
    city: str
    state: str
    country: str


@strawberry.type
class CountrySchema:
    id: int
    name: str

@strawberry.type
class AdmissionStatsSchema:
    application_fee: int
    admission_type: str
    gpa_min: decimal.Decimal
    gpa_max: decimal.Decimal
    sat_min: decimal.Decimal
    sat_max: decimal.Decimal
    act_min: decimal.Decimal
    act_max: decimal.Decimal
    ielts_min: decimal.Decimal
    ielts_max: decimal.Decimal


@strawberry.type
class WorkOpportunitySchema:
    id: int
    name: str


@strawberry.type
class UniversityContactSchema:
    id: int
    name: str
    designation: str
    email: str
    phone: str


@strawberry.type
class UniversityStatsSchema:
    id: int
    name: str
    value: str


@strawberry.type
class UniversityVideoLinkSchema:
    id: int
    url: str


@strawberry.type
class RankingAgencySchema:
    id: int
    name: str
    description: str
    logo: str


@strawberry.type
class UniversityRankingSchema:
    rank: str
    ranking_agency: RankingAgencySchema


@strawberry.type
class UniversityFAQSchema:
    id: int
    question: str
    answer: str


@strawberry.type
class PartnerAgencySchema:
    id: int
    name: str
    partner_type: str


@strawberry.type
class UniversitySchema:
    id: int
    cover_url: str
    name: str
    type: str
    establish_year: int
    status: str
    about: str
    review_rating: decimal.Decimal
    avg_acceptance_rate: int
    avg_tution_fee: int

    location: LocationSchema

    admission_stats: List[AdmissionStatsSchema]
    work_opportunities: List[WorkOpportunitySchema]
    contacts: List[UniversityContactSchema]
    statistics: List[UniversityStatsSchema]
    video_links: List[UniversityVideoLinkSchema]
    rankings: List[UniversityRankingSchema]
    faqs: List[UniversityFAQSchema]

@strawberry.type
class UniversityListSchema:
    id: int
    name: str
    type: str
    establish_year: int
    status: str
    country: str

    @classmethod
    def get_universities(
            cls,
            auth_token: str,
            page: int,
            limit: Optional[int] = 50,
            country: Optional[str] = None,
            query: Optional[str] = None,
            sort_by_id_asc: Optional[bool] = False,
    ) -> List["UniversityListSchema"]:

        try:
            auth_token = uuid.UUID(auth_token)
            Employee.objects.get(authToken=auth_token)
        except ValueError:
            raise GraphQLError("Invalid auth token")
        except Employee.DoesNotExist:
            raise GraphQLError("Employee does not exist")

        if page < 1:
            raise GraphQLError("Page must be greater than 0")

        limit = limit or 50
        limit = min(limit, 100)
        offset = (page - 1) * limit

        country = country.strip() if country else None
        query = query.strip() if query else None

        university_table = university._meta.db_table
        location_table = location._meta.db_table

        order_by = "u.id ASC" if sort_by_id_asc else "u.id DESC"

        sql = f"""
            SELECT
                u.id,
                u.name,
                u.type,
                u.establish_year,
                u.status,
                l.country
            FROM {university_table} u
            JOIN {location_table} l ON u.location_id = l.id
            WHERE
                (%s IS NULL OR LOWER(l.country) = LOWER(%s))
                AND (%s IS NULL OR LOWER(u.name) LIKE LOWER(%s))
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """

        params = [
            country,
            country,
            query,
            f"%{query}%" if query else None,
            limit,
            offset,
        ]

        with connection.cursor() as cursor:
            cursor.execute(sql, params)

            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return [
            UniversityListSchema(
                id=row["id"],
                name=row["name"],
                type=row["type"],
                establish_year=row["establish_year"],
                status=row["status"],
                country=row["country"],
            )
            for row in rows
        ]

@strawberry.type
class UniversityQuery:
    get_university_list : List[UniversityListSchema] = strawberry.field(
        resolver= UniversityListSchema.get_universities,
    )
