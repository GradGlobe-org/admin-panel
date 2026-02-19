import strawberry
from typing import Optional, List
import decimal
from  dataclasses import dataclass

# This file exists because GraphQL makes you be explicit about everything.


# ==========================================================
# COUNTRY – FAQ
# ==========================================================
@dataclass
class CountryFaqBase:
    question: str
    answer: str


@strawberry.input
class CountryFaqInput(CountryFaqBase):
    pass


@strawberry.input
class CountryFaqUpdate(CountryFaqBase):
    id: int


@strawberry.type
class CountryFaqSchema(CountryFaqBase):
    id: int


@strawberry.input
class CountryFaqUpdateInput:
    add: Optional[List[CountryFaqInput]] = None
    update: Optional[List[CountryFaqUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ==========================================================
# WHY STUDY IN
# ==========================================================
@dataclass
class WhyStudyInSectionBase:
    content: str


@strawberry.input
class WhyStudyInSectionInput(WhyStudyInSectionBase):
    pass


@strawberry.input
class WhyStudyInSectionUpdate(WhyStudyInSectionBase):
    id: int


@strawberry.type
class WhyStudyInSectionSchema(WhyStudyInSectionBase):
    id: int


@strawberry.input
class WhyStudyInSectionUpdateInput:
    add: Optional[List[WhyStudyInSectionInput]] = None
    update: Optional[List[WhyStudyInSectionUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ==========================================================
# COUNTRY FACTS
# ==========================================================
@dataclass
class CountryFactBase:
    name: str


@strawberry.input
class CountryFactInput(CountryFactBase):
    pass


@strawberry.input
class CountryFactUpdate(CountryFactBase):
    id: int


@strawberry.type
class CountryFactSchema(CountryFactBase):
    id: int


@strawberry.input
class CountryFactUpdateInput:
    add: Optional[List[CountryFactInput]] = None
    update: Optional[List[CountryFactUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ==========================================================
# COST OF LIVING
# ==========================================================
@dataclass
class CostOfLivingBase:
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


@strawberry.input
class CostOfLivingInput(CostOfLivingBase):
    pass


@strawberry.input
class CostOfLivingUpdate(CostOfLivingBase):
    id: int


@strawberry.type
class CostOfLivingSchema(CostOfLivingBase):
    id: int


@strawberry.input
class CostOfLivingUpdateInput:
    add: Optional[List[CostOfLivingInput]] = None
    update: Optional[List[CostOfLivingUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ==========================================================
# VISA
# ==========================================================
@dataclass
class VisaBase:
    name: str
    type_of_visa: str
    cost: int
    describe: str


@strawberry.input
class VisaInput(VisaBase):
    pass


@strawberry.input
class VisaUpdate(VisaBase):
    id: int


@strawberry.type
class VisaSchema(VisaBase):
    id: int


@strawberry.input
class VisaUpdateInput:
    add: Optional[List[VisaInput]] = None
    update: Optional[List[VisaUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ==========================================================
# COUNTRY CORE
# ==========================================================
@dataclass
class CountryBase:
    name: str


@strawberry.input
class CountryInput(CountryBase):
    pass


@strawberry.input
class CountryItemUpdate(CountryBase):
    id: int


@strawberry.type
class CountrySchema(CountryBase):
    pass

@strawberry.input
class CountryUpdateInput:
    add: Optional[List[CountryInput]] = None
    update: Optional[List[CountryItemUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ---------------- Admission Stats ----------------
@dataclass
class AdmissionStatsBase:
    application_fee: Optional[int] = None
    admission_type: Optional[str] = None
    gpa_min: Optional[decimal.Decimal] = None
    gpa_max: Optional[decimal.Decimal] = None
    sat_min: Optional[decimal.Decimal] = None
    sat_max: Optional[decimal.Decimal] = None
    act_min: Optional[decimal.Decimal] = None
    act_max: Optional[decimal.Decimal] = None
    ielts_min: Optional[decimal.Decimal] = None
    ielts_max: Optional[decimal.Decimal] = None

@strawberry.input
class AdmissionStatsInput(AdmissionStatsBase):
    pass

@strawberry.input
class AdmissionStatsUpdateItemInput(AdmissionStatsBase):
    id: int

@strawberry.type
class AdmissionStatsSchema(AdmissionStatsBase):
    id: int

@strawberry.input
class AdmissionStatsUpdateInput:
    add: Optional[List[AdmissionStatsInput]] = None
    update: Optional[List[AdmissionStatsUpdateItemInput]] = None
    delete_ids: Optional[List[int]] = None


# ---------------- Work Opportunities ----------------
@dataclass
class WorkOpportunityBase:
    name: str

@strawberry.input
class WorkOpportunityInput(WorkOpportunityBase):
    pass

@strawberry.input
class WorkOpportunityUpdate(WorkOpportunityBase):
    id: int

@strawberry.type
class WorkOpportunitySchema(WorkOpportunityBase):
    id: int

@strawberry.input
class WorkOpportunityUpdateInput:
    add: Optional[List[WorkOpportunityInput]] = None
    update: Optional[List[WorkOpportunityUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ---------------- University Contacts ----------------
@dataclass
class UniversityContactBase:
    name: str
    designation: str
    email: str
    phone: str

@strawberry.input
class UniversityContactInput(UniversityContactBase):
    pass

@strawberry.input
class UniversityContactUpdate(UniversityContactBase):
    id: int

@strawberry.type
class UniversityContactSchema(UniversityContactBase):
    id: int

@strawberry.input
class UniversityContactUpdateInput:
    add: Optional[List[UniversityContactInput]] = None
    update: Optional[List[UniversityContactUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ---------------- University Stats ----------------
@dataclass
class UniversityStatBase:
    name: str
    value: str

@strawberry.input
class UniversityStatInput(UniversityStatBase):
    pass

@strawberry.input
class UniversityStatUpdate(UniversityStatBase):
    id: int

@strawberry.type
class UniversityStatsSchema(UniversityStatBase):
    id: int

@strawberry.input
class UniversityStatUpdateInput:
    add: Optional[List[UniversityStatInput]] = None
    update: Optional[List[UniversityStatUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ---------------- Video Links ----------------
@dataclass
class UniversityVideoLinkBase:
    url: str

@strawberry.input
class UniversityVideoLinkInput(UniversityVideoLinkBase):
    pass

@strawberry.input
class UniversityVideoLinkUpdate(UniversityVideoLinkBase):
    id: int

@strawberry.type
class UniversityVideoLinkSchema(UniversityVideoLinkBase):
    id: int

@strawberry.input
class UniversityVideoLinkUpdateInput:
    add: Optional[List[UniversityVideoLinkInput]] = None
    update: Optional[List[UniversityVideoLinkUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ---------------- Rankings ----------------
@dataclass
class RankingAgencyBase:
    name: str
    description: str
    logo: str

@strawberry.type
class RankingSchema(RankingAgencyBase):
    id : int

@dataclass
class UniversityRankingBase:
    rank: str
    ranking_agency_id: int

@strawberry.input
class UniversityRankingInput(UniversityRankingBase):
    pass

@strawberry.input
class UniversityRankingUpdate(UniversityRankingBase):
    id: int

@strawberry.type
class UniversityRankingSchema:
    id: int
    rank: str
    ranking_agency: RankingSchema

@strawberry.input
class UniversityRankingUpdateInput:
    add: Optional[List[UniversityRankingInput]] = None
    update: Optional[List[UniversityRankingUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ---------------- FAQs ----------------
@dataclass
class UniversityFAQBase:
    question: str
    answer: str

@strawberry.input
class UniversityFAQInput(UniversityFAQBase):
    pass

@strawberry.input
class UniversityFAQUpdate(UniversityFAQBase):
    id: int

@strawberry.type
class UniversityFAQSchema(UniversityFAQBase):
    id: int

@strawberry.input
class UniversityFAQUpdateInput:
    add: Optional[List[UniversityFAQInput]] = None
    update: Optional[List[UniversityFAQUpdate]] = None
    delete_ids: Optional[List[int]] = None


# ---------------- Location ----------------
@dataclass
class LocationBase:
    city: str
    state: str
    country: str

@strawberry.input
class LocationInput(LocationBase):
    pass

@strawberry.input
class LocationUpdate(LocationBase):
    id: int

@strawberry.type
class LocationSchema(LocationBase):
    id: int


# ---------------- University ----------------

@dataclass
class UniversityBase:
    cover_url: str
    name: str
    type: str
    establish_year: int
    status: str
    about: str
    admission_requirements: str
    location_map_link: str
    review_rating: decimal.Decimal
    avg_acceptance_rate: int
    avg_tution_fee: int

@strawberry.input
class UniversityInput(UniversityBase):
    pass

@strawberry.input
class UniversityPatch:
    cover_url: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    establish_year: Optional[int] = None
    status: Optional[str] = None
    about: Optional[str] = None
    admission_requirements: Optional[str] = None
    location_map_link: Optional[str] = None
    review_rating: Optional[decimal.Decimal] = None
    avg_acceptance_rate: Optional[int] = None
    avg_tution_fee: Optional[int] = None

@strawberry.type
class UniversitySchema(UniversityBase):
    id: int

from strawberry.file_uploads import Upload

@dataclass
class AskDocumentBase:
    document_type_id: int
    instructions: Optional[str] = None

@strawberry.input
class AskDocumentInput(AskDocumentBase):
    document: Optional[Upload] = None

@dataclass
class UpdateDocumentBase:
    id: int
    instructions: Optional[str] = None

@strawberry.input
class UpdateDocumentInput(UpdateDocumentBase):
    document: Optional[Upload] = None
    status: Optional[str] = None
    comment: Optional[str] = None

@strawberry.input
class DocumentRequirementUpdateInput:
    add: Optional[List[AskDocumentInput]] = None
    update: Optional[List[UpdateDocumentInput]] = None
    delete_ids: Optional[List[int]] = None

@dataclass
class SubMilestoneUpdateBase:
    id: int
    status: Optional[str] = None
    counsellor_comment: Optional[str] = None

@strawberry.input
class SubMilestoneUpdateInput(SubMilestoneUpdateBase):
    pass


@strawberry.input
class MilestoneUpdateInput:
    update: Optional[List[SubMilestoneUpdateInput]] = None