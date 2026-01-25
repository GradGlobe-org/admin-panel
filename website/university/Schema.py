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

    @classmethod
    def get_detailed_university(cls,
                                auth_token: str,
                                uni_id: int,
                                ):

        try:
            auth_token = uuid.UUID(auth_token)
            Employee.objects.get(authToken=auth_token)
        except ValueError:
            raise GraphQLError("Invalid auth token")
        except Employee.DoesNotExist:
            raise GraphQLError("Employee does not exist")

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT get_detailed_university(%s)",
                    [uni_id]
                )
                row = cursor.fetchone()
        except:
            raise GraphQLError("Error fetching University details")

        if not row or not row[0]:
            raise GraphQLError("University not found")

        try:
            data = row[0]

            return cls(
                id=data["id"],
                cover_url=data["cover_url"],
                name=data["name"],
                type=data["type"],
                establish_year=data["establish_year"],
                status=data["status"],
                about=data["about"],
                review_rating=data["review_rating"],
                avg_acceptance_rate=data["avg_acceptance_rate"],
                avg_tution_fee=data["avg_tution_fee"],

                location=LocationSchema(
                    id=data["location"]["id"],
                    city=data["location"]["city"],
                    state=data["location"]["state"],
                    country=data["location"]["country"],
                ),

                admission_stats=[
                    AdmissionStatsSchema(
                        application_fee=a["application_fee"],
                        admission_type=a["admission_type"],
                        gpa_min=a["gpa_min"],
                        gpa_max=a["gpa_max"],
                        sat_min=a["sat_min"],
                        sat_max=a["sat_max"],
                        act_min=a["act_min"],
                        act_max=a["act_max"],
                        ielts_min=a["ielts_min"],
                        ielts_max=a["ielts_max"],
                    )
                    for a in data.get("admission_stats", [])
                ],

                work_opportunities=[
                    WorkOpportunitySchema(
                        id=w["id"],
                        name=w["name"]
                    )
                    for w in data.get("work_opportunities", [])
                ],

                contacts=[
                    UniversityContactSchema(
                        id=c["id"],
                        name=c["name"],
                        designation=c["designation"],
                        email=c["email"],
                        phone=c["phone"],
                    )
                    for c in data.get("contacts", [])
                ],

                statistics=[
                    UniversityStatsSchema(
                        id=s["id"],
                        name=s["name"],
                        value=s["value"],
                    )
                    for s in data.get("statistics", [])
                ],

                video_links=[
                    UniversityVideoLinkSchema(
                        id=v["id"],
                        url=v["url"],
                    )
                    for v in data.get("video_links", [])
                ],

                rankings=[
                    UniversityRankingSchema(
                        rank=r["rank"],
                        ranking_agency=RankingAgencySchema(
                            id=r["ranking_agency"]["id"],
                            name=r["ranking_agency"]["name"],
                            description=r["ranking_agency"]["description"],
                            logo=r["ranking_agency"]["logo"],
                        )
                    )
                    for r in data.get("rankings", [])
                ],

                faqs=[
                    UniversityFAQSchema(
                        id=f["id"],
                        question=f["question"],
                        answer=f["answer"],
                    )
                    for f in data.get("faqs", [])
                ],
            )

        except:
            raise GraphQLError("Internal server error")


    # @classmethod
    # def add_new_university(cls
    #
    #                        ):


@strawberry.type
class UniversityQuery:
    get_university_list : List[UniversityListSchema] = strawberry.field(
        resolver= UniversityListSchema.get_universities,
    )

    get_detailed_university : UniversitySchema = strawberry.field(
        resolver= UniversitySchema.get_detailed_university,
    )
