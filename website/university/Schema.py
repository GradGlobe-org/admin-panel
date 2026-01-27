import math
import uuid
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, transaction, IntegrityError
from authentication.Utils import SchemaMixin
from authentication.models import Employee
from strawberry.exceptions import GraphQLError
from university.models import *
from .AllSchemas import *
from django.db.models import Q
from website.utils import EmployeeAuthorization


@strawberry.type
class UniversitySchema(SchemaMixin):
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
    location_map_link: str

    location: Optional[LocationSchema] = None

    admission_stats: Optional[List[AdmissionStatsSchema]] = None
    work_opportunities: Optional[List[WorkOpportunitySchema]] = None
    contacts: Optional[List[UniversityContactSchema]] = None
    statistics: Optional[List[UniversityStatsSchema]] = None
    video_links: Optional[List[UniversityVideoLinkSchema]] = None
    rankings: Optional[List[UniversityRankingSchema]] = None
    faqs: Optional[List[UniversityFAQSchema]] = None

    @classmethod
    def university_schema_builder(cls,data: dict) -> "UniversitySchema":
        try:
            return UniversitySchema(
                id=data["id"],
                cover_url=data["cover_url"],
                name=data["name"],
                type=data["type"],
                establish_year=data["establish_year"],
                status=data["status"],
                about=data["about"],
                location_map_link=data["location_map_link"],
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
                        id=a["id"],
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
                    for a in (data.get("admission_stats") or [])
                ],

                work_opportunities=[
                    WorkOpportunitySchema(
                        id=w["id"],
                        name=w["name"],
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
                        id=r["id"],
                        rank=r["rank"],
                        ranking_agency=RankingSchema(
                            id=r["ranking_agency"]["id"],
                            name=r["ranking_agency"]["name"],
                            description=r["ranking_agency"]["description"],
                            logo=r["ranking_agency"]["logo"],
                        ),
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
        except Exception:
            raise GraphQLError("Internal server error")


    @classmethod
    def get_detailed_university(cls,
                                auth_token: str,
                                uni_id: int,
                                ) -> "UniversitySchema":

        if not cls.get_employee(auth_token):
            raise GraphQLError("Invalid Auth token")

        # emp = cls.get_employee(auth_token)
        #
        # print(emp.job_roles.all())
        # permission_names = set()
        #
        # for role in emp.job_roles.all():
        #     permission_names.update(
        #         role.permissions.values_list("name", flat=True)
        #     )
        #
        # print(list(permission_names))

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT get_detailed_university(%s)",
                    [uni_id]
                )
                row = cursor.fetchone()
        except Exception:
            raise GraphQLError("Error fetching University details")

        if not row or not row[0]:
            raise GraphQLError("University not found")

        try:
            return cls.university_schema_builder(data=row[0])
        except Exception as e:
            raise (GraphQLError(str(e)))

    @classmethod
    def add_new_university(
            cls,
            auth_token: str,
            basic_details: UniversityInput,
            loc_id: Optional[int] = None,
            loc: Optional[LocationInput] = None,
            admission_stats: Optional[List[AdmissionStatsInput]] = None,
            work_opportunities: Optional[List[WorkOpportunityInput]] = None,
            contacts: Optional[List[UniversityContactInput]] = None,
            statistics: Optional[List[UniversityStatInput]] = None,
            video_links: Optional[List[UniversityVideoLinkInput]] = None,
            rankings: Optional[List[UniversityRankingInput]] = None,
            uni_faqs: Optional[List[UniversityFAQInput]] = None,
    ) -> "UniversitySchema":

        if not cls.get_employee(auth_token):
            raise GraphQLError("Invalid Auth Token")

        if loc_id and loc:
            raise GraphQLError("Provide either loc_id or loc, not both")

        if not loc_id and not loc:
            raise GraphQLError("Location is required")

        if university.objects.filter(
                Q(name__iexact=basic_details.name.strip()) |
                Q(cover_url=basic_details.cover_url.strip()) |
                Q(location_map_link=basic_details.location_map_link.strip())
        ).exists():
            raise GraphQLError("University already exists")

        for field, value in vars(basic_details).items():
            if value is None:
                continue

            if field == "type" and value not in ("PUBLIC", "PRIVATE"):
                raise GraphQLError("University type must be PUBLIC or PRIVATE")

            if field == "status" and value not in ("DRAFT", "PUBLISH"):
                raise GraphQLError("Invalid status")

            if field == "review_rating" and not (0 <= value <= 5):
                raise GraphQLError("Rating must be between 0 and 5")

            if field == "avg_acceptance_rate" and not (0 <= value <= 100):
                raise GraphQLError("Acceptance rate must be 0–100")

        try:
            with transaction.atomic():

                if loc_id:
                    try:
                        new_location = location.objects.get(id=loc_id)
                    except location.DoesNotExist:
                        raise GraphQLError("Invalid location id")
                else:
                    new_location, _ = location.objects.get_or_create(
                        city__iexact=loc.city.strip(),
                        state__iexact=loc.state.strip(),
                        country__iexact=loc.country.strip(),
                        defaults={
                            "city": loc.city.strip(),
                            "state": loc.state.strip(),
                            "country": loc.country.strip(),
                        }
                    )

                new_university = university.objects.create(
                    name=basic_details.name.strip(),
                    cover_url=basic_details.cover_url.strip(),
                    type=basic_details.type,
                    establish_year=basic_details.establish_year,
                    status=basic_details.status,
                    about=basic_details.about,
                    admission_requirements=basic_details.admission_requirements,
                    location_map_link=basic_details.location_map_link.strip(),
                    review_rating=basic_details.review_rating,
                    avg_acceptance_rate=basic_details.avg_acceptance_rate,
                    avg_tution_fee=basic_details.avg_tution_fee,
                    location=new_location,
                )

                def nz(value, default):
                    return value if value is not None else default

                if admission_stats:
                    AdmissionStats.objects.bulk_create([
                        AdmissionStats(
                            university=new_university,
                            application_fee=nz(a.application_fee, 0),
                            admission_type=nz(a.admission_type, ""),
                            GPA_min=nz(a.gpa_min, decimal.Decimal("0")),
                            GPA_max=nz(a.gpa_max, decimal.Decimal("0")),
                            SAT_min=nz(a.sat_min, decimal.Decimal("0")),
                            SAT_max=nz(a.sat_max, decimal.Decimal("0")),
                            ACT_min=nz(a.act_min, decimal.Decimal("0")),
                            ACT_max=nz(a.act_max, decimal.Decimal("0")),
                            IELTS_min=nz(a.ielts_min, decimal.Decimal("0")),
                            IELTS_max=nz(a.ielts_max, decimal.Decimal("0")),
                        )
                        for a in admission_stats
                    ])

                if work_opportunities:
                    WorkOpportunity.objects.bulk_create([
                        WorkOpportunity(university=new_university, name=w.name)
                        for w in work_opportunities
                    ])

                if contacts:
                    Uni_contact.objects.bulk_create([
                        Uni_contact(
                            university=new_university,
                            name=c.name,
                            designation=c.designation,
                            email=c.email,
                            phone=c.phone,
                        )
                        for c in contacts
                    ])

                if statistics:
                    stats.objects.bulk_create([
                        stats(university=new_university, name=s.name, value=s.value)
                        for s in statistics
                    ])

                if video_links:
                    videos_links.objects.bulk_create([
                        videos_links(university=new_university, url=v.url)
                        for v in video_links
                    ])

                if rankings:
                    university_ranking.objects.bulk_create([
                        university_ranking(
                            university=new_university,
                            rank=r.rank,
                            ranking_agency_id=r.ranking_agency_id,
                        )
                        for r in rankings
                    ])

                if uni_faqs:
                    faqs.objects.bulk_create([
                        faqs(
                            university=new_university,
                            question=f.question,
                            answer=f.answer,
                        )
                        for f in uni_faqs
                    ])

            with connection.cursor() as cursor:
                cursor.execute("SELECT get_detailed_university(%s)", [new_university.id])
                row = cursor.fetchone()

            if not row or not row[0]:
                raise GraphQLError("University created but could not be fetched")

            return cls.university_schema_builder(data=row[0])

        except IntegrityError:
            raise GraphQLError("Duplicate entry violates a unique constraint")

        except GraphQLError:
            raise

        except Exception as e:
            raise GraphQLError(f"Unexpected error: {str(e)}")

    @classmethod
    def edit_university(
            cls,
            uni_id: int,
            auth_token: str,
            uni_data: Optional[UniversityPatch] = None,
            admission_stats: Optional[AdmissionStatsUpdateInput] = None,
            work_opportunities: Optional[WorkOpportunityUpdateInput] = None,
            contacts: Optional[UniversityContactUpdateInput] = None,
            statistics: Optional[UniversityStatUpdateInput] = None,
            videolinks: Optional[UniversityVideoLinkUpdateInput] = None,
            rankings: Optional[UniversityRankingUpdateInput] = None,
            uni_faqs: Optional[UniversityFAQUpdateInput] = None,
    ) -> "UniversitySchema":

        if not cls.get_employee(auth_token):
            raise GraphQLError("Invalid Auth Token")

        try:
            with transaction.atomic():

                uni = (
                    university.objects
                    .select_for_update()
                    .filter(id=uni_id)
                    .first()
                )
                if not uni:
                    raise GraphQLError("University does not exist")

                # ---------------- BASE PATCH ----------------
                if uni_data:
                    for field, value in vars(uni_data).items():
                        if value is None:
                            continue

                        if field == "type" and value not in ("PUBLIC", "PRIVATE"):
                            raise GraphQLError("University type must be PUBLIC or PRIVATE")

                        if field == "status" and value not in ("DRAFT", "PUBLISH"):
                            raise GraphQLError("Invalid status")

                        if field == "review_rating" and not (0 <= value <= 5):
                            raise GraphQLError("Rating must be between 0 and 5")

                        if field == "avg_acceptance_rate" and not (0 <= value <= 100):
                            raise GraphQLError("Acceptance rate must be 0–100")

                        setattr(uni, field, value)
                    uni.save()

                # ---------------- GENERIC HANDLER ----------------
                def handle_update(model, payload, create_map, update_map, label: str):
                    if not payload:
                        return {"added": 0, "updated": 0, "deleted": 0}

                    added = updated = deleted = 0

                    if payload.delete_ids:
                        deleted, _ = model.objects.filter(
                            id__in=payload.delete_ids,
                            university_id=uni_id
                        ).delete()

                        if deleted != len(payload.delete_ids):
                            raise GraphQLError(
                                f"{label}: Delete failed (expected {len(payload.delete_ids)}, deleted {deleted})"
                            )

                    if payload.update:
                        for obj in payload.update:
                            data = {
                                model_field: getattr(obj, input_field)
                                for model_field, input_field in update_map.items()
                                if getattr(obj, input_field) is not None
                            }

                            rows = model.objects.filter(
                                id=obj.id,
                                university_id=uni_id
                            ).update(**data)

                            if rows != 1:
                                raise GraphQLError(
                                    f"{label}: Update failed for ID {obj.id}"
                                )

                            updated += 1

                    if payload.add:
                        created = model.objects.bulk_create([
                            model(
                                university_id=uni_id,
                                **{
                                    model_field: getattr(obj, input_field)
                                    for model_field, input_field in create_map.items()
                                }
                            )
                            for obj in payload.add
                        ])

                        added = len(created)

                    return {"added": added, "updated": updated, "deleted": deleted}

                # ---------------- ADMISSION STATS (SPECIAL MAP) ----------------
                admission_map = {
                    "application_fee": "application_fee",
                    "admission_type": "admission_type",
                    "GPA_min": "gpa_min",
                    "GPA_max": "gpa_max",
                    "SAT_min": "sat_min",
                    "SAT_max": "sat_max",
                    "ACT_min": "act_min",
                    "ACT_max": "act_max",
                    "IELTS_min": "ielts_min",
                    "IELTS_max": "ielts_max",
                }

                # ---------------- SIMPLE TABLES ----------------
                simple = lambda *f: ({x: x for x in f}, {x: x for x in f})

                handle_update(
                    AdmissionStats,
                    admission_stats,
                    admission_map,
                    admission_map,
                    "AdmissionStats"
                )

                handle_update(
                    WorkOpportunity,
                    work_opportunities,
                    *simple("name"),
                    "WorkOpportunities"
                )

                handle_update(
                    Uni_contact,
                    contacts,
                    *simple("name", "designation", "email", "phone"),
                    "Contacts"
                )

                handle_update(
                    stats,
                    statistics,
                    *simple("name", "value"),
                    "Statistics"
                )

                handle_update(
                    videos_links,
                    videolinks,
                    *simple("url"),
                    "VideoLinks"
                )

                handle_update(
                    university_ranking,
                    rankings,
                    *simple("rank", "ranking_agency_id"),
                    "Rankings"
                )

                handle_update(
                    faqs,
                    uni_faqs,
                    *simple("question", "answer"),
                    "FAQs"
                )

            # ---------------- FETCH RESULT ----------------
            with connection.cursor() as cursor:
                cursor.execute("SELECT get_detailed_university(%s)", [uni_id])
                row = cursor.fetchone()

            if not row or not row[0]:
                raise GraphQLError("University not found")

            return cls.university_schema_builder(data=row[0])

        except GraphQLError:
            raise
        except Exception as e:
            raise GraphQLError(f"Update failed: {str(e)}")

@strawberry.type
class UniversityOutputSchema(EmployeeAuthorization, SchemaMixin):
    limit : int
    current_page: int
    total_count: int
    universities: List[UniversitySchema]


    @classmethod
    def get_universities(
            cls,
            auth_token: str,
            country: Optional[str] = None,
            query: Optional[str] = None,
            sort_by_id_asc: Optional[bool] = False,
            page: int = 1,
            limit: Optional[int] = 50,
    ) -> "UniversityOutputSchema":

        if not cls.get_employee(auth_token):
            raise GraphQLError("Invalid Auth Token")
        if page < 1:
            raise GraphQLError("Page must be greater than 0")

        limit = min(limit or 50, 100)
        offset = (page - 1) * limit
        country = country.strip() if country else None
        query = query.strip() if query else None
        university_table = university._meta.db_table
        location_table = location._meta.db_table
        order_by = "u.id ASC" if sort_by_id_asc else "u.id DESC"
        sql = f"""
        SELECT
            u.id              AS university_id,
            u.cover_url,
            u.name,
            u.type,
            u.establish_year,
            u.status,
            u.about,
            u.review_rating,
            u.avg_acceptance_rate,
            u.avg_tution_fee,
            u.location_map_link,

            l.id              AS location_id,
            l.city,
            l.state,
            l.country,

            COUNT(*) OVER()   AS total_count
        FROM {university_table} u
        JOIN {location_table} l ON u.location_id = l.id
        WHERE
            (%s IS NULL OR LOWER(l.country) = LOWER(%s))
            AND (%s IS NULL OR LOWER(u.name) LIKE LOWER(%s))
        ORDER BY {order_by}
        LIMIT %s OFFSET %s;
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

        total_count = rows[0]["total_count"] if rows else 0

        universities = [
            UniversitySchema(
                id=row["university_id"],
                cover_url=row["cover_url"],
                name=row["name"],
                type=row["type"],
                establish_year=row["establish_year"],
                status=row["status"],
                about=row["about"],
                review_rating=row["review_rating"],
                avg_acceptance_rate=row["avg_acceptance_rate"],
                avg_tution_fee=row["avg_tution_fee"],
                location_map_link=row["location_map_link"],

                location=LocationSchema(
                    id=row["location_id"],
                    city=row["city"],
                    state=row["state"],
                    country=row["country"],
                ),

                admission_stats=None,
                work_opportunities=None,
                contacts=None,
                statistics=None,
                video_links=None,
                rankings=None,
                faqs=None,
            )
            for row in rows
        ]

        return cls(
            limit=limit,
            current_page=page,
            total_count=total_count,
            universities=universities,
        )


@strawberry.type
class UniversityQuery:
    get_university_list : UniversityOutputSchema = strawberry.field(
        resolver= UniversityOutputSchema.get_universities,
    )

    get_detailed_university : UniversitySchema = strawberry.field(
        resolver= UniversitySchema.get_detailed_university,
    )

@strawberry.type
class UniversityMutation:
    add_new_university : UniversitySchema = strawberry.field(
        resolver= UniversitySchema.add_new_university,
    )

    edit_university : UniversitySchema = strawberry.field(
        resolver= UniversitySchema.edit_university,
    )
